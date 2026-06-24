from decimal import Decimal
from pathlib import Path

import click

from infrastructure.config_repository import ConfigRepository
from infrastructure.data_repository import DataRepository
from service.backup_service import BackupService
from service.csv_service import CsvService
from service.transaction_service import TransactionService

_DB_PATH = Path.home() / ".stock-analyzer" / "data.db"
_CONFIG_PATH = Path("config.json")


def _tx_svc() -> TransactionService:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TransactionService(DataRepository(str(_DB_PATH)), ConfigRepository(str(_CONFIG_PATH)))


def _csv_svc() -> CsvService:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return CsvService(DataRepository(str(_DB_PATH)))


def _backup_svc() -> BackupService:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return BackupService(DataRepository(str(_DB_PATH)))


@click.command("summary")
@click.argument("plan_id")
def summary(plan_id):
    """保有状況サマリーを表示する"""
    try:
        s = _tx_svc().get_portfolio_summary(plan_id)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(f"保有株数          : {s.shares_held}")
    click.echo(f"平均取得単価(奨励込): {s.avg_cost_with} 円")
    click.echo(f"平均取得単価(拠出のみ): {s.avg_cost_without} 円")
    click.echo(f"累計拠出金額      : {s.total_contribution} 円")
    click.echo(f"累計実現損益(奨励込): {s.realized_gain_loss_with} 円")
    click.echo(f"累計実現損益(拠出のみ): {s.realized_gain_loss_without} 円")


@click.command("simulate")
@click.argument("plan_id")
@click.option("--price", required=True, help="現在株価（円）")
@click.option("--shares", default=None, help="売却株数（省略時は全株）")
def simulate(plan_id, price, shares):
    """売却シミュレーションを実行する"""
    try:
        current_price = Decimal(price)
    except Exception:
        raise click.BadParameter(f"数値ではありません: {price!r}")
    sim_shares = None
    if shares is not None:
        try:
            sim_shares = Decimal(shares)
        except Exception:
            raise click.BadParameter(f"数値ではありません: {shares!r}")
    try:
        result = _tx_svc().simulate_sale(plan_id, current_price, sim_shares)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(f"シミュレーション株数  : {result.simulation_shares}")
    click.echo(f"売却益(奨励込)       : {result.gain_loss_with} 円")
    click.echo(f"売却益(拠出のみ)      : {result.gain_loss_without} 円")
    click.echo(f"推定税額(奨励込)      : {result.tax_with} 円")
    click.echo(f"推定税額(拠出のみ)    : {result.tax_without} 円")
    click.echo(f"税引後手取り(奨励込)  : {result.net_proceeds_with} 円")
    click.echo(f"税引後手取り(拠出のみ): {result.net_proceeds_without} 円")


@click.group("csv")
def csv_cmd():
    """CSVエクスポート／インポート"""


@csv_cmd.command("export")
@click.argument("plan_id")
@click.argument("output_path")
def csv_export(plan_id, output_path):
    """取引をCSVにエクスポートする"""
    try:
        count = _csv_svc().export(plan_id, output_path)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(f"{count} 件をエクスポートしました: {output_path}")


@csv_cmd.command("import")
@click.argument("plan_id")
@click.argument("input_path")
def csv_import(plan_id, input_path):
    """CSVから取引をインポートする"""
    svc = _csv_svc()
    rows, errors = svc.validate(input_path)
    if errors:
        click.echo("バリデーションエラーが発生しました:", err=True)
        for e in errors:
            click.echo(f"  {e}", err=True)
        raise click.Abort()
    tx_svc = _tx_svc()
    for row in rows:
        kwargs = svc.parse_row(row)
        tt = kwargs.pop("transaction_type")
        d = kwargs.pop("transaction_date")
        tx_svc.add_transaction(plan_id, tt, d, **kwargs)
    click.echo(f"{len(rows)} 件をインポートしました。")


@click.group("backup")
def backup():
    """バックアップのエクスポート／インポート"""


@backup.command("export")
@click.argument("output_path")
def backup_export(output_path):
    """全データをJSONにエクスポートする"""
    try:
        plans, txs = _backup_svc().export_backup(output_path)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(f"エクスポート完了: 持株会 {plans} 件, 取引 {txs} 件 → {output_path}")


@backup.command("import")
@click.argument("input_path")
@click.confirmation_option(prompt="既存データに上書きインポートします。よいですか？")
def backup_import(input_path):
    """バックアップJSONからインポートする（上書き）"""
    try:
        plans, txs = _backup_svc().import_backup(input_path)
    except Exception as e:
        raise click.ClickException(str(e))
    click.echo(f"インポート完了: 持株会 {plans} 件, 取引 {txs} 件")
