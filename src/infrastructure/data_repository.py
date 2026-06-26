import sqlite3
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional

from domain.models import Plan, Transaction, TransactionType


def _d(value) -> Optional[Decimal]:
    return Decimal(value) if value is not None else None


def _s(value) -> Optional[str]:
    return str(value) if value is not None else None


class DataRepository:
    def __init__(self, db_path: str = "data.db"):
        self._db_path = db_path
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        schema_path = Path(__file__).parent / "schema.sql"
        with open(schema_path, encoding="utf-8") as f:
            schema = f.read()
        with self._connect() as conn:
            conn.executescript(schema)
            self._migrate(conn)

    def _migrate(self, conn: sqlite3.Connection) -> None:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(transactions)").fetchall()}
        for col in ("carryover_amount", "employee_carryover_amount"):
            if col not in existing:
                conn.execute(f"ALTER TABLE transactions ADD COLUMN {col} TEXT")

    # ── Plan ──────────────────────────────────────────────────────────────

    def save_plan(self, plan: Plan) -> None:
        sql = """
            INSERT INTO plans VALUES (?,?,?,?,?,?,?,?)
            ON CONFLICT(plan_id) DO UPDATE SET
                company_name = excluded.company_name,
                ticker       = excluded.ticker,
                start_date   = excluded.start_date,
                end_date     = excluded.end_date,
                is_active    = excluded.is_active,
                updated_at   = excluded.updated_at
        """
        with self._connect() as conn:
            conn.execute(sql, (
                plan.plan_id,
                plan.company_name,
                plan.ticker,
                plan.start_date.isoformat(),
                plan.end_date.isoformat() if plan.end_date else None,
                1 if plan.is_active else 0,
                plan.created_at.isoformat(),
                plan.updated_at.isoformat(),
            ))

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM plans WHERE plan_id = ?", (plan_id,)
            ).fetchone()
        return self._row_to_plan(row) if row else None

    def list_plans(self) -> list[Plan]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM plans ORDER BY created_at"
            ).fetchall()
        return [self._row_to_plan(r) for r in rows]

    def _row_to_plan(self, row) -> Plan:
        return Plan(
            plan_id=row["plan_id"],
            company_name=row["company_name"],
            ticker=row["ticker"],
            start_date=date.fromisoformat(row["start_date"]),
            end_date=date.fromisoformat(row["end_date"]) if row["end_date"] else None,
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    # ── Transaction ───────────────────────────────────────────────────────

    def save_transaction(self, tx: Transaction) -> None:
        sql = """
            INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                transaction_type          = excluded.transaction_type,
                transaction_date          = excluded.transaction_date,
                shares_quantity           = excluded.shares_quantity,
                contribution_amount       = excluded.contribution_amount,
                incentive_amount          = excluded.incentive_amount,
                dividend_amount           = excluded.dividend_amount,
                sale_price_per_share      = excluded.sale_price_per_share,
                split_ratio_before        = excluded.split_ratio_before,
                split_ratio_after         = excluded.split_ratio_after,
                avg_cost_with             = excluded.avg_cost_with,
                avg_cost_without          = excluded.avg_cost_without,
                shares_held_after         = excluded.shares_held_after,
                realized_gain_loss_with   = excluded.realized_gain_loss_with,
                realized_gain_loss_without = excluded.realized_gain_loss_without,
                carryover_amount          = excluded.carryover_amount,
                employee_carryover_amount = excluded.employee_carryover_amount,
                updated_at                = excluded.updated_at
        """
        with self._connect() as conn:
            conn.execute(sql, self._tx_to_tuple(tx))

    def save_transactions_bulk(self, transactions: list[Transaction]) -> None:
        sql = """
            INSERT INTO transactions VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                avg_cost_with             = excluded.avg_cost_with,
                avg_cost_without          = excluded.avg_cost_without,
                shares_held_after         = excluded.shares_held_after,
                realized_gain_loss_with   = excluded.realized_gain_loss_with,
                realized_gain_loss_without = excluded.realized_gain_loss_without,
                employee_carryover_amount = excluded.employee_carryover_amount,
                updated_at                = excluded.updated_at
        """
        with self._connect() as conn:
            conn.executemany(sql, [self._tx_to_tuple(t) for t in transactions])

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM transactions WHERE transaction_id = ?",
                (transaction_id,),
            ).fetchone()
        return self._row_to_tx(row) if row else None

    def list_transactions(self, plan_id: str) -> list[Transaction]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE plan_id = ?"
                " ORDER BY transaction_date, created_at",
                (plan_id,),
            ).fetchall()
        return [self._row_to_tx(r) for r in rows]

    def list_transactions_from_date(self, plan_id: str, from_date: date) -> list[Transaction]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM transactions WHERE plan_id = ? AND transaction_date >= ?"
                " ORDER BY transaction_date, created_at",
                (plan_id, from_date.isoformat()),
            ).fetchall()
        return [self._row_to_tx(r) for r in rows]

    def get_latest_transaction_before(
        self, plan_id: str, before_date: date
    ) -> Optional[Transaction]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM transactions WHERE plan_id = ? AND transaction_date < ?"
                " ORDER BY transaction_date DESC, created_at DESC LIMIT 1",
                (plan_id, before_date.isoformat()),
            ).fetchone()
        return self._row_to_tx(row) if row else None

    def delete_transaction(self, transaction_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM transactions WHERE transaction_id = ?", (transaction_id,)
            )

    def _tx_to_tuple(self, tx: Transaction) -> tuple:
        return (
            tx.transaction_id,
            tx.plan_id,
            tx.transaction_type.value,
            tx.transaction_date.isoformat(),
            _s(tx.shares_quantity),
            _s(tx.contribution_amount),
            _s(tx.incentive_amount),
            _s(tx.dividend_amount),
            _s(tx.sale_price_per_share),
            tx.split_ratio_before,
            tx.split_ratio_after,
            _s(tx.avg_cost_with),
            _s(tx.avg_cost_without),
            _s(tx.shares_held_after),
            _s(tx.realized_gain_loss_with),
            _s(tx.realized_gain_loss_without),
            _s(tx.carryover_amount),
            _s(tx.employee_carryover_amount),
            tx.created_at.isoformat(),
            tx.updated_at.isoformat(),
        )

    def get_latest_contribution_before(
        self, plan_id: str, before_date: date
    ) -> Optional[Transaction]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM transactions WHERE plan_id = ? AND transaction_date < ?"
                " AND transaction_type = ?"
                " ORDER BY transaction_date DESC, created_at DESC LIMIT 1",
                (plan_id, before_date.isoformat(), TransactionType.CONTRIBUTION.value),
            ).fetchone()
        return self._row_to_tx(row) if row else None

    def _row_to_tx(self, row) -> Transaction:
        return Transaction(
            transaction_id=row["transaction_id"],
            plan_id=row["plan_id"],
            transaction_type=TransactionType(row["transaction_type"]),
            transaction_date=date.fromisoformat(row["transaction_date"]),
            shares_quantity=_d(row["shares_quantity"]),
            contribution_amount=_d(row["contribution_amount"]),
            incentive_amount=_d(row["incentive_amount"]),
            dividend_amount=_d(row["dividend_amount"]),
            sale_price_per_share=_d(row["sale_price_per_share"]),
            split_ratio_before=row["split_ratio_before"],
            split_ratio_after=row["split_ratio_after"],
            avg_cost_with=_d(row["avg_cost_with"]),
            avg_cost_without=_d(row["avg_cost_without"]),
            shares_held_after=_d(row["shares_held_after"]),
            realized_gain_loss_with=_d(row["realized_gain_loss_with"]),
            realized_gain_loss_without=_d(row["realized_gain_loss_without"]),
            carryover_amount=_d(row["carryover_amount"]),
            employee_carryover_amount=_d(row["employee_carryover_amount"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
