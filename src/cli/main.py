import os
from pathlib import Path

import click

from infrastructure.config_repository import ConfigRepository
from infrastructure.data_repository import DataRepository
from service.plan_service import PlanService
from service.transaction_service import TransactionService
from service.csv_service import CsvService
from service.backup_service import BackupService

_DB_PATH = Path.home() / ".stock-analyzer" / "data.db"
_CONFIG_PATH = Path("config.json")


def _make_repo() -> DataRepository:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return DataRepository(str(_DB_PATH))


@click.group()
def cli():
    """社員持株会管理ツール"""


# ── サブグループ登録はコマンドモジュールの import で行う ──────────────────────
from cli.plan_commands import plan  # noqa: E402
from cli.transaction_commands import transaction  # noqa: E402
from cli.summary_commands import summary, simulate, csv_cmd, backup  # noqa: E402

cli.add_command(plan)
cli.add_command(transaction)
cli.add_command(summary)
cli.add_command(simulate)
cli.add_command(csv_cmd)
cli.add_command(backup)
