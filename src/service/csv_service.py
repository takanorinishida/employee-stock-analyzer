import csv
from datetime import date
from decimal import Decimal
from typing import Optional

from domain.models import TransactionType
from infrastructure.data_repository import DataRepository

_EXPORT_FIELDS = [
    "transaction_date",
    "transaction_type",
    "shares_quantity",
    "contribution_amount",
    "incentive_amount",
    "dividend_amount",
    "sale_price_per_share",
    "split_ratio_before",
    "split_ratio_after",
    "avg_cost_with",
    "avg_cost_without",
    "shares_held_after",
    "realized_gain_loss_with",
    "realized_gain_loss_without",
]

_IMPORT_FIELDS = [
    "transaction_date",
    "transaction_type",
    "shares_quantity",
    "contribution_amount",
    "incentive_amount",
    "dividend_amount",
    "sale_price_per_share",
    "split_ratio_before",
    "split_ratio_after",
]

_TYPE_REQUIRED: dict[TransactionType, list[str]] = {
    TransactionType.CONTRIBUTION: ["contribution_amount", "incentive_amount", "shares_quantity"],
    TransactionType.DIVIDEND_REINVESTMENT: ["dividend_amount", "shares_quantity"],
    TransactionType.SALE: ["sale_price_per_share", "shares_quantity"],
    TransactionType.STOCK_SPLIT: ["split_ratio_before", "split_ratio_after"],
    TransactionType.REVERSE_SPLIT: ["split_ratio_before", "split_ratio_after"],
}


class CsvService:
    def __init__(self, repo: DataRepository):
        self._repo = repo

    def export(self, plan_id: str, output_path: str) -> int:
        transactions = self._repo.list_transactions(plan_id)
        with open(output_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=_EXPORT_FIELDS)
            writer.writeheader()
            for tx in transactions:
                writer.writerow({
                    "transaction_date": tx.transaction_date.isoformat(),
                    "transaction_type": tx.transaction_type.value,
                    "shares_quantity": str(tx.shares_quantity) if tx.shares_quantity is not None else "",
                    "contribution_amount": str(tx.contribution_amount) if tx.contribution_amount is not None else "",
                    "incentive_amount": str(tx.incentive_amount) if tx.incentive_amount is not None else "",
                    "dividend_amount": str(tx.dividend_amount) if tx.dividend_amount is not None else "",
                    "sale_price_per_share": str(tx.sale_price_per_share) if tx.sale_price_per_share is not None else "",
                    "split_ratio_before": str(tx.split_ratio_before) if tx.split_ratio_before is not None else "",
                    "split_ratio_after": str(tx.split_ratio_after) if tx.split_ratio_after is not None else "",
                    "avg_cost_with": str(tx.avg_cost_with),
                    "avg_cost_without": str(tx.avg_cost_without),
                    "shares_held_after": str(tx.shares_held_after),
                    "realized_gain_loss_with": str(tx.realized_gain_loss_with) if tx.realized_gain_loss_with is not None else "",
                    "realized_gain_loss_without": str(tx.realized_gain_loss_without) if tx.realized_gain_loss_without is not None else "",
                })
        return len(transactions)

    def validate(self, input_path: str) -> tuple[list[dict], list[str]]:
        """CSVを検証し (行データリスト, エラーリスト) を返す。エラーなしなら全件返却。"""
        errors: list[str] = []
        rows: list[dict] = []
        try:
            with open(input_path, encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for line_num, row in enumerate(reader, start=2):
                    row_errors = self._validate_row(row, line_num)
                    if row_errors:
                        errors.extend(row_errors)
                    else:
                        rows.append(row)
        except FileNotFoundError:
            errors.append(f"ファイルが見つかりません: {input_path}")
        except Exception as e:
            errors.append(f"ファイル読み込みエラー: {e}")
        return rows, errors

    def parse_row(self, row: dict) -> dict:
        """検証済みの行データをサービス層が受け取れる形式に変換する"""
        tt = TransactionType(row["transaction_type"])
        result: dict = {
            "transaction_type": tt,
            "transaction_date": date.fromisoformat(row["transaction_date"]),
        }
        if row.get("shares_quantity"):
            result["shares_quantity"] = Decimal(row["shares_quantity"])
        if row.get("contribution_amount"):
            result["contribution_amount"] = Decimal(row["contribution_amount"])
        if row.get("incentive_amount"):
            result["incentive_amount"] = Decimal(row["incentive_amount"])
        if row.get("dividend_amount"):
            result["dividend_amount"] = Decimal(row["dividend_amount"])
        if row.get("sale_price_per_share"):
            result["sale_price_per_share"] = Decimal(row["sale_price_per_share"])
        if row.get("split_ratio_before"):
            result["split_ratio_before"] = int(row["split_ratio_before"])
        if row.get("split_ratio_after"):
            result["split_ratio_after"] = int(row["split_ratio_after"])
        return result

    def _validate_row(self, row: dict, line: int) -> list[str]:
        errors: list[str] = []
        prefix = f"行 {line}: "

        # transaction_date
        raw_date = row.get("transaction_date", "").strip()
        try:
            date.fromisoformat(raw_date)
        except ValueError:
            errors.append(f"{prefix}transaction_date が無効です（値: {raw_date!r}）")

        # transaction_type
        raw_type = row.get("transaction_type", "").strip()
        try:
            tt = TransactionType(raw_type)
        except ValueError:
            errors.append(f"{prefix}transaction_type が無効です（値: {raw_type!r}）")
            return errors

        # 型別必須フィールド
        for field in _TYPE_REQUIRED.get(tt, []):
            if not row.get(field, "").strip():
                errors.append(f"{prefix}{field} は {tt.value} に必須です")

        # 数値フィールドの形式チェック
        for field in ["shares_quantity", "contribution_amount", "incentive_amount",
                      "dividend_amount", "sale_price_per_share"]:
            val = row.get(field, "").strip()
            if val:
                try:
                    Decimal(val)
                except Exception:
                    errors.append(f"{prefix}{field} が数値ではありません（値: {val!r}）")
        for field in ["split_ratio_before", "split_ratio_after"]:
            val = row.get(field, "").strip()
            if val:
                try:
                    int(val)
                except Exception:
                    errors.append(f"{prefix}{field} が整数ではありません（値: {val!r}）")

        return errors
