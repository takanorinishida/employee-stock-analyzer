"""CsvService のバリデーション・エクスポート・インポートテスト"""
import sys
import csv
from decimal import Decimal
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from domain.models import TransactionType
from infrastructure.data_repository import DataRepository
from service.csv_service import CsvService

D = Decimal


def _make_svc(tmp_path):
    db_path = str(tmp_path / "test.db")
    return CsvService(DataRepository(db_path))


def _write_csv(path: Path, rows: list[dict], fieldnames=None):
    if not fieldnames:
        fieldnames = list(rows[0].keys())
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


# ── バリデーション ───────────────────────────────────────────────────────

class TestValidate:
    def test_valid_contribution_row(self, tmp_path):
        csv_path = tmp_path / "in.csv"
        _write_csv(csv_path, [{
            "transaction_date": "2024-01-10",
            "transaction_type": "CONTRIBUTION",
            "shares_quantity": "10",
            "contribution_amount": "10000",
            "incentive_amount": "500",
            "dividend_amount": "",
            "sale_price_per_share": "",
            "split_ratio_before": "",
            "split_ratio_after": "",
        }])
        rows, errors = _make_svc(tmp_path).validate(str(csv_path))
        assert errors == []
        assert len(rows) == 1

    def test_invalid_date(self, tmp_path):
        csv_path = tmp_path / "in.csv"
        _write_csv(csv_path, [{
            "transaction_date": "not-a-date",
            "transaction_type": "CONTRIBUTION",
            "shares_quantity": "10",
            "contribution_amount": "10000",
            "incentive_amount": "500",
            "dividend_amount": "", "sale_price_per_share": "",
            "split_ratio_before": "", "split_ratio_after": "",
        }])
        rows, errors = _make_svc(tmp_path).validate(str(csv_path))
        assert any("transaction_date" in e for e in errors)

    def test_invalid_transaction_type(self, tmp_path):
        csv_path = tmp_path / "in.csv"
        _write_csv(csv_path, [{
            "transaction_date": "2024-01-10",
            "transaction_type": "UNKNOWN",
            "shares_quantity": "", "contribution_amount": "",
            "incentive_amount": "", "dividend_amount": "",
            "sale_price_per_share": "", "split_ratio_before": "", "split_ratio_after": "",
        }])
        rows, errors = _make_svc(tmp_path).validate(str(csv_path))
        assert any("transaction_type" in e for e in errors)

    def test_missing_required_field_for_type(self, tmp_path):
        csv_path = tmp_path / "in.csv"
        _write_csv(csv_path, [{
            "transaction_date": "2024-01-10",
            "transaction_type": "CONTRIBUTION",
            "shares_quantity": "",  # 必須なのに空
            "contribution_amount": "10000",
            "incentive_amount": "500",
            "dividend_amount": "", "sale_price_per_share": "",
            "split_ratio_before": "", "split_ratio_after": "",
        }])
        rows, errors = _make_svc(tmp_path).validate(str(csv_path))
        assert any("shares_quantity" in e for e in errors)

    def test_non_numeric_decimal_field(self, tmp_path):
        csv_path = tmp_path / "in.csv"
        _write_csv(csv_path, [{
            "transaction_date": "2024-01-10",
            "transaction_type": "CONTRIBUTION",
            "shares_quantity": "abc",
            "contribution_amount": "10000",
            "incentive_amount": "500",
            "dividend_amount": "", "sale_price_per_share": "",
            "split_ratio_before": "", "split_ratio_after": "",
        }])
        rows, errors = _make_svc(tmp_path).validate(str(csv_path))
        assert any("shares_quantity" in e for e in errors)

    def test_file_not_found(self, tmp_path):
        rows, errors = _make_svc(tmp_path).validate(str(tmp_path / "nonexistent.csv"))
        assert any("見つかりません" in e for e in errors)

    def test_multiple_valid_rows(self, tmp_path):
        csv_path = tmp_path / "in.csv"
        _write_csv(csv_path, [
            {
                "transaction_date": "2024-01-10",
                "transaction_type": "CONTRIBUTION",
                "shares_quantity": "10",
                "contribution_amount": "10000",
                "incentive_amount": "500",
                "dividend_amount": "", "sale_price_per_share": "",
                "split_ratio_before": "", "split_ratio_after": "",
            },
            {
                "transaction_date": "2024-02-10",
                "transaction_type": "SALE",
                "shares_quantity": "5",
                "contribution_amount": "",
                "incentive_amount": "",
                "dividend_amount": "",
                "sale_price_per_share": "1300",
                "split_ratio_before": "", "split_ratio_after": "",
            },
        ])
        rows, errors = _make_svc(tmp_path).validate(str(csv_path))
        assert errors == []
        assert len(rows) == 2


# ── parse_row ─────────────────────────────────────────────────────────────

class TestParseRow:
    def test_contribution(self):
        row = {
            "transaction_date": "2024-01-10",
            "transaction_type": "CONTRIBUTION",
            "shares_quantity": "10",
            "contribution_amount": "10000",
            "incentive_amount": "500",
            "dividend_amount": "",
            "sale_price_per_share": "",
            "split_ratio_before": "",
            "split_ratio_after": "",
        }
        svc = CsvService(None)  # parse_row は repo 不要
        result = svc.parse_row(row)
        assert result["transaction_type"] == TransactionType.CONTRIBUTION
        assert result["transaction_date"] == date(2024, 1, 10)
        assert result["shares_quantity"] == D("10")
        assert result["contribution_amount"] == D("10000")
        assert result["incentive_amount"] == D("500")
        assert "dividend_amount" not in result

    def test_stock_split(self):
        row = {
            "transaction_date": "2024-06-01",
            "transaction_type": "STOCK_SPLIT",
            "shares_quantity": "",
            "contribution_amount": "", "incentive_amount": "",
            "dividend_amount": "", "sale_price_per_share": "",
            "split_ratio_before": "1",
            "split_ratio_after": "2",
        }
        svc = CsvService(None)
        result = svc.parse_row(row)
        assert result["transaction_type"] == TransactionType.STOCK_SPLIT
        assert result["split_ratio_before"] == 1
        assert result["split_ratio_after"] == 2
