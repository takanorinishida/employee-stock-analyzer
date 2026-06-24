"""TransactionService の統合テスト（インメモリ SQLite 使用）"""
import sys
from decimal import Decimal
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.models import TransactionType
from infrastructure.config_repository import ConfigRepository
from infrastructure.data_repository import DataRepository
from service.plan_service import PlanService
from service.transaction_service import TransactionService

D = Decimal


def _make_services(tmp_path):
    db_path = str(tmp_path / "test.db")
    repo = DataRepository(db_path)
    config_path = str(tmp_path / "config.json")
    import json
    Path(config_path).write_text(json.dumps({"capital_gains_tax_rate": "0.20315"}))
    config = ConfigRepository(config_path)
    plan_svc = PlanService(repo)
    tx_svc = TransactionService(repo, config)
    return plan_svc, tx_svc


def _create_plan(plan_svc):
    return plan_svc.create_plan("T001", "テスト会社", date(2024, 1, 1))


# ── 取引追加 ──────────────────────────────────────────────────────────────

class TestAddTransaction:
    def test_contribution_from_zero(self, tmp_path):
        plan_svc, tx_svc = _make_services(tmp_path)
        plan = _create_plan(plan_svc)
        tx = tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 1, 10),
            shares_quantity=D("10"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        assert tx.shares_held_after == D("10.0000")
        assert tx.avg_cost_with == D("1050.00")
        assert tx.avg_cost_without == D("1000.00")

    def test_second_contribution(self, tmp_path):
        plan_svc, tx_svc = _make_services(tmp_path)
        plan = _create_plan(plan_svc)
        tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 1, 10),
            shares_quantity=D("10"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        tx = tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 2, 10),
            shares_quantity=D("9"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        assert tx.shares_held_after == D("19.0000")
        assert tx.avg_cost_with == D("1105.26")
        assert tx.avg_cost_without == D("1052.63")

    def test_sale_reduces_shares(self, tmp_path):
        plan_svc, tx_svc = _make_services(tmp_path)
        plan = _create_plan(plan_svc)
        tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 1, 10),
            shares_quantity=D("20"), contribution_amount=D("20000"), incentive_amount=D("0"),
        )
        tx = tx_svc.add_transaction(
            plan.plan_id, TransactionType.SALE, date(2024, 3, 1),
            shares_quantity=D("5"), sale_price_per_share=D("1300"),
        )
        assert tx.shares_held_after == D("15.0000")
        assert tx.realized_gain_loss_with is not None


# ── 取引編集と再計算 ──────────────────────────────────────────────────────

class TestEditTransaction:
    def _setup(self, tmp_path):
        plan_svc, tx_svc = _make_services(tmp_path)
        plan = _create_plan(plan_svc)
        tx1 = tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 1, 10),
            shares_quantity=D("10"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        tx2 = tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 2, 10),
            shares_quantity=D("9"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        return tx_svc, plan.plan_id, tx1, tx2

    def test_edit_recalculates_subsequent(self, tmp_path):
        tx_svc, plan_id, tx1, tx2 = self._setup(tmp_path)
        # tx1 の株数を変更 → tx2 も再計算されるはず
        tx_svc.edit_transaction(tx1.transaction_id, shares_quantity=D("5"))
        txs = tx_svc.list_transactions(plan_id)
        # tx1: 5 株になる
        assert txs[0].shares_held_after == D("5.0000")
        # tx2: prev_shares=5 で再計算される
        assert txs[1].shares_held_after == D("14.0000")

    def test_edit_date_triggers_recalc(self, tmp_path):
        tx_svc, plan_id, tx1, tx2 = self._setup(tmp_path)
        # tx2 の日付を tx1 より前に変更
        tx_svc.edit_transaction(tx2.transaction_id, transaction_date=date(2024, 1, 5))
        txs = tx_svc.list_transactions(plan_id)
        # 日付昇順で tx2(1/5) が先になる
        assert txs[0].transaction_date == date(2024, 1, 5)
        assert txs[1].transaction_date == date(2024, 1, 10)


# ── 取引削除と再計算 ──────────────────────────────────────────────────────

class TestDeleteTransaction:
    def test_delete_recalculates_subsequent(self, tmp_path):
        plan_svc, tx_svc = _make_services(tmp_path)
        plan = _create_plan(plan_svc)
        tx1 = tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 1, 10),
            shares_quantity=D("10"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        tx2 = tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 2, 10),
            shares_quantity=D("9"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        tx_svc.delete_transaction(tx1.transaction_id)
        txs = tx_svc.list_transactions(plan.plan_id)
        assert len(txs) == 1
        # tx2 が最初の取引になるので prev_shares=0 から再計算
        assert txs[0].shares_held_after == D("9.0000")


# ── PortfolioSummary ──────────────────────────────────────────────────────

class TestPortfolioSummary:
    def test_empty_plan(self, tmp_path):
        plan_svc, tx_svc = _make_services(tmp_path)
        plan = _create_plan(plan_svc)
        s = tx_svc.get_portfolio_summary(plan.plan_id)
        assert s.shares_held == D("0")
        assert s.total_contribution == D("0")

    def test_summary_after_transactions(self, tmp_path):
        plan_svc, tx_svc = _make_services(tmp_path)
        plan = _create_plan(plan_svc)
        tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 1, 10),
            shares_quantity=D("10"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        tx_svc.add_transaction(
            plan.plan_id, TransactionType.CONTRIBUTION, date(2024, 2, 10),
            shares_quantity=D("9"), contribution_amount=D("10000"), incentive_amount=D("500"),
        )
        s = tx_svc.get_portfolio_summary(plan.plan_id)
        assert s.shares_held == D("19.0000")
        assert s.total_contribution == D("20000")
        assert s.realized_gain_loss_with == D("0")
