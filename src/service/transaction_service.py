from datetime import date, datetime
from decimal import Decimal
from typing import Optional
import uuid

from domain.models import Transaction, TransactionType
from domain.portfolio import PortfolioSummary, SaleSimulation
from infrastructure.config_repository import ConfigRepository
from infrastructure.data_repository import DataRepository
import service.calculation_engine as engine

_ZERO = Decimal("0")

_EDITABLE_FIELDS = frozenset({
    "transaction_date",
    "shares_quantity",
    "contribution_amount",
    "incentive_amount",
    "dividend_amount",
    "sale_price_per_share",
    "split_ratio_before",
    "split_ratio_after",
    "carryover_amount",
})


class TransactionService:
    def __init__(self, repo: DataRepository, config: ConfigRepository):
        self._repo = repo
        self._config = config

    # ── 追加 ──────────────────────────────────────────────────────────────

    def add_transaction(
        self,
        plan_id: str,
        transaction_type: TransactionType,
        transaction_date: date,
        **kwargs,
    ) -> Transaction:
        prev = self._repo.get_latest_transaction_before(plan_id, transaction_date)
        prev_shares = prev.shares_held_after if prev else _ZERO
        prev_avg_with = prev.avg_cost_with if prev else _ZERO
        prev_avg_without = prev.avg_cost_without if prev else _ZERO

        prev_contrib = self._repo.get_latest_contribution_before(plan_id, transaction_date)
        prev_carryover = prev_contrib.carryover_amount or _ZERO if prev_contrib else _ZERO
        prev_employee_carryover = (
            prev_contrib.employee_carryover_amount or _ZERO if prev_contrib else _ZERO
        )

        tx = self._build_transaction(
            plan_id, transaction_type, transaction_date,
            prev_shares, prev_avg_with, prev_avg_without,
            prev_carryover, prev_employee_carryover,
            **kwargs,
        )
        self._repo.save_transaction(tx)
        return tx

    # ── 編集 ──────────────────────────────────────────────────────────────

    def edit_transaction(self, transaction_id: str, **kwargs) -> Transaction:
        tx = self._get_or_raise(transaction_id)
        old_date = tx.transaction_date

        for key, value in kwargs.items():
            if key in _EDITABLE_FIELDS and value is not None:
                setattr(tx, key, value)

        tx.updated_at = datetime.now()
        self._repo.save_transaction(tx)

        recalc_date = min(old_date, tx.transaction_date)
        self._recalculate_from(tx.plan_id, recalc_date)
        return self._repo.get_transaction(transaction_id)

    # ── 削除 ──────────────────────────────────────────────────────────────

    def delete_transaction(self, transaction_id: str) -> None:
        tx = self._get_or_raise(transaction_id)
        plan_id = tx.plan_id
        affected_date = tx.transaction_date
        self._repo.delete_transaction(transaction_id)
        self._recalculate_from(plan_id, affected_date)

    # ── 参照 ──────────────────────────────────────────────────────────────

    def list_transactions(self, plan_id: str) -> list[Transaction]:
        return self._repo.list_transactions(plan_id)

    def get_portfolio_summary(self, plan_id: str) -> PortfolioSummary:
        transactions = self._repo.list_transactions(plan_id)
        if not transactions:
            return PortfolioSummary(
                shares_held=_ZERO,
                avg_cost_with=_ZERO,
                avg_cost_without=_ZERO,
                total_contribution=_ZERO,
                realized_gain_loss_with=_ZERO,
                realized_gain_loss_without=_ZERO,
            )
        latest = transactions[-1]
        total_contribution = sum(
            (tx.contribution_amount or _ZERO) for tx in transactions
        )
        total_gain_with = sum(
            (tx.realized_gain_loss_with or _ZERO) for tx in transactions
        )
        total_gain_without = sum(
            (tx.realized_gain_loss_without or _ZERO) for tx in transactions
        )
        return PortfolioSummary(
            shares_held=latest.shares_held_after,
            avg_cost_with=latest.avg_cost_with,
            avg_cost_without=latest.avg_cost_without,
            total_contribution=total_contribution,
            realized_gain_loss_with=total_gain_with,
            realized_gain_loss_without=total_gain_without,
        )

    def simulate_sale(
        self,
        plan_id: str,
        current_price: Decimal,
        simulation_shares: Optional[Decimal] = None,
    ) -> SaleSimulation:
        summary = self.get_portfolio_summary(plan_id)
        shares = simulation_shares if simulation_shares is not None else summary.shares_held
        tax_rate = self._config.get_tax_rate()
        return engine.simulate_sale(
            current_price, shares,
            summary.avg_cost_with, summary.avg_cost_without,
            tax_rate,
        )

    # ── 内部: 全件再計算 ──────────────────────────────────────────────────

    def _recalculate_from(self, plan_id: str, from_date: date) -> None:
        prev = self._repo.get_latest_transaction_before(plan_id, from_date)
        prev_shares = prev.shares_held_after if prev else _ZERO
        prev_avg_with = prev.avg_cost_with if prev else _ZERO
        prev_avg_without = prev.avg_cost_without if prev else _ZERO

        prev_contrib = self._repo.get_latest_contribution_before(plan_id, from_date)
        prev_carryover = prev_contrib.carryover_amount or _ZERO if prev_contrib else _ZERO
        prev_employee_carryover = (
            prev_contrib.employee_carryover_amount or _ZERO if prev_contrib else _ZERO
        )

        affected = self._repo.list_transactions_from_date(plan_id, from_date)
        updated = []
        for tx in affected:
            tx, prev_carryover, prev_employee_carryover = self._apply_calc(
                tx, prev_shares, prev_avg_with, prev_avg_without,
                prev_carryover, prev_employee_carryover,
            )
            prev_shares = tx.shares_held_after
            prev_avg_with = tx.avg_cost_with
            prev_avg_without = tx.avg_cost_without
            updated.append(tx)

        if updated:
            self._repo.save_transactions_bulk(updated)

    def _apply_calc(
        self,
        tx: Transaction,
        prev_shares: Decimal,
        prev_avg_with: Decimal,
        prev_avg_without: Decimal,
        prev_carryover: Decimal = _ZERO,
        prev_employee_carryover: Decimal = _ZERO,
    ) -> tuple[Transaction, Decimal, Decimal]:
        tt = tx.transaction_type
        if tt == TransactionType.CONTRIBUTION:
            carryover = tx.carryover_amount or _ZERO
            shares, avg_with, avg_without, new_emp_carryover = engine.calc_contribution(
                prev_shares, prev_avg_with, prev_avg_without,
                tx.shares_quantity, tx.contribution_amount, tx.incentive_amount,
                prev_carryover, carryover, prev_employee_carryover,
            )
            tx.shares_held_after = shares
            tx.avg_cost_with = avg_with
            tx.avg_cost_without = avg_without
            tx.employee_carryover_amount = new_emp_carryover
            next_carryover = carryover
            next_employee_carryover = new_emp_carryover

        elif tt == TransactionType.DIVIDEND_REINVESTMENT:
            shares, avg_with, avg_without = engine.calc_dividend_reinvestment(
                prev_shares, prev_avg_with, prev_avg_without,
                tx.shares_quantity, tx.dividend_amount,
            )
            tx.shares_held_after = shares
            tx.avg_cost_with = avg_with
            tx.avg_cost_without = avg_without
            next_carryover = prev_carryover
            next_employee_carryover = prev_employee_carryover

        elif tt == TransactionType.SALE:
            shares, avg_with, avg_without, gain_with, gain_without = engine.calc_sale(
                prev_shares, prev_avg_with, prev_avg_without,
                tx.shares_quantity, tx.sale_price_per_share,
            )
            tx.shares_held_after = shares
            tx.avg_cost_with = avg_with
            tx.avg_cost_without = avg_without
            tx.realized_gain_loss_with = gain_with
            tx.realized_gain_loss_without = gain_without
            next_carryover = prev_carryover
            next_employee_carryover = prev_employee_carryover

        elif tt in (TransactionType.STOCK_SPLIT, TransactionType.REVERSE_SPLIT):
            shares, avg_with, avg_without = engine.calc_split(
                prev_shares, prev_avg_with, prev_avg_without,
                tx.split_ratio_before, tx.split_ratio_after,
            )
            tx.shares_held_after = shares
            tx.avg_cost_with = avg_with
            tx.avg_cost_without = avg_without
            next_carryover = prev_carryover
            next_employee_carryover = prev_employee_carryover

        else:
            next_carryover = prev_carryover
            next_employee_carryover = prev_employee_carryover

        tx.updated_at = datetime.now()
        return tx, next_carryover, next_employee_carryover

    def _build_transaction(
        self,
        plan_id: str,
        transaction_type: TransactionType,
        transaction_date: date,
        prev_shares: Decimal,
        prev_avg_with: Decimal,
        prev_avg_without: Decimal,
        prev_carryover: Decimal = _ZERO,
        prev_employee_carryover: Decimal = _ZERO,
        **kwargs,
    ) -> Transaction:
        valid = {k: v for k, v in kwargs.items() if k in _EDITABLE_FIELDS - {"transaction_date"}}
        now = datetime.now()
        tx = Transaction(
            transaction_id=str(uuid.uuid4()),
            plan_id=plan_id,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            avg_cost_with=_ZERO,
            avg_cost_without=_ZERO,
            shares_held_after=_ZERO,
            created_at=now,
            updated_at=now,
            **valid,
        )
        tx, _, _ = self._apply_calc(
            tx, prev_shares, prev_avg_with, prev_avg_without,
            prev_carryover, prev_employee_carryover,
        )
        return tx

    def _get_or_raise(self, transaction_id: str) -> Transaction:
        tx = self._repo.get_transaction(transaction_id)
        if tx is None:
            raise ValueError(f"取引が見つかりません: {transaction_id}")
        return tx
