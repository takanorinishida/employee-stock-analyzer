import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from domain.models import Plan, Transaction, TransactionType
from infrastructure.data_repository import DataRepository


def _serialize(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    raise TypeError(f"型 {type(obj)} はシリアライズできません")


class BackupService:
    def __init__(self, repo: DataRepository):
        self._repo = repo

    def export_backup(self, output_path: str) -> tuple[int, int]:
        """全データをJSONにエクスポート。(plan件数, transaction件数) を返す。"""
        plans = self._repo.list_plans()
        transactions: list[Transaction] = []
        for plan in plans:
            transactions.extend(self._repo.list_transactions(plan.plan_id))

        data = {
            "exported_at": datetime.now().isoformat(),
            "plans": [self._plan_to_dict(p) for p in plans],
            "transactions": [self._tx_to_dict(t) for t in transactions],
        }
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=_serialize)

        return len(plans), len(transactions)

    def import_backup(self, input_path: str) -> tuple[int, int]:
        """バックアップJSONを全件インポート（上書き）。(plan件数, transaction件数) を返す。"""
        with open(input_path, encoding="utf-8") as f:
            data = json.load(f)

        for plan_data in data.get("plans", []):
            self._repo.save_plan(self._dict_to_plan(plan_data))

        for tx_data in data.get("transactions", []):
            self._repo.save_transaction(self._dict_to_tx(tx_data))

        return len(data.get("plans", [])), len(data.get("transactions", []))

    # ── 変換ヘルパー ───────────────────────────────────────────────────────

    def _plan_to_dict(self, plan: Plan) -> dict:
        return {
            "plan_id": plan.plan_id,
            "company_name": plan.company_name,
            "ticker": plan.ticker,
            "start_date": plan.start_date.isoformat(),
            "end_date": plan.end_date.isoformat() if plan.end_date else None,
            "is_active": plan.is_active,
            "created_at": plan.created_at.isoformat(),
            "updated_at": plan.updated_at.isoformat(),
        }

    def _dict_to_plan(self, d: dict) -> Plan:
        return Plan(
            plan_id=d["plan_id"],
            company_name=d["company_name"],
            ticker=d.get("ticker"),
            start_date=date.fromisoformat(d["start_date"]),
            end_date=date.fromisoformat(d["end_date"]) if d.get("end_date") else None,
            is_active=d["is_active"],
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
        )

    def _tx_to_dict(self, tx: Transaction) -> dict:
        def opt_d(v) -> str | None:
            return str(v) if v is not None else None

        return {
            "transaction_id": tx.transaction_id,
            "plan_id": tx.plan_id,
            "transaction_type": tx.transaction_type.value,
            "transaction_date": tx.transaction_date.isoformat(),
            "shares_quantity": opt_d(tx.shares_quantity),
            "contribution_amount": opt_d(tx.contribution_amount),
            "incentive_amount": opt_d(tx.incentive_amount),
            "dividend_amount": opt_d(tx.dividend_amount),
            "sale_price_per_share": opt_d(tx.sale_price_per_share),
            "split_ratio_before": tx.split_ratio_before,
            "split_ratio_after": tx.split_ratio_after,
            "avg_cost_with": str(tx.avg_cost_with),
            "avg_cost_without": str(tx.avg_cost_without),
            "shares_held_after": str(tx.shares_held_after),
            "realized_gain_loss_with": opt_d(tx.realized_gain_loss_with),
            "realized_gain_loss_without": opt_d(tx.realized_gain_loss_without),
            "created_at": tx.created_at.isoformat(),
            "updated_at": tx.updated_at.isoformat(),
        }

    def _dict_to_tx(self, d: dict) -> Transaction:
        def opt_d(v) -> Decimal | None:
            return Decimal(v) if v is not None else None

        return Transaction(
            transaction_id=d["transaction_id"],
            plan_id=d["plan_id"],
            transaction_type=TransactionType(d["transaction_type"]),
            transaction_date=date.fromisoformat(d["transaction_date"]),
            shares_quantity=opt_d(d.get("shares_quantity")),
            contribution_amount=opt_d(d.get("contribution_amount")),
            incentive_amount=opt_d(d.get("incentive_amount")),
            dividend_amount=opt_d(d.get("dividend_amount")),
            sale_price_per_share=opt_d(d.get("sale_price_per_share")),
            split_ratio_before=d.get("split_ratio_before"),
            split_ratio_after=d.get("split_ratio_after"),
            avg_cost_with=Decimal(d["avg_cost_with"]),
            avg_cost_without=Decimal(d["avg_cost_without"]),
            shares_held_after=Decimal(d["shares_held_after"]),
            realized_gain_loss_with=opt_d(d.get("realized_gain_loss_with")),
            realized_gain_loss_without=opt_d(d.get("realized_gain_loss_without")),
            created_at=datetime.fromisoformat(d["created_at"]),
            updated_at=datetime.fromisoformat(d["updated_at"]),
        )
