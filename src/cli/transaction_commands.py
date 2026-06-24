from datetime import date
from decimal import Decimal
from pathlib import Path

import click

from domain.models import TransactionType
from infrastructure.config_repository import ConfigRepository
from infrastructure.data_repository import DataRepository
from service.transaction_service import TransactionService

_DB_PATH = Path.home() / ".stock-analyzer" / "data.db"
_CONFIG_PATH = Path("config.json")

_TYPE_CHOICES = [t.value for t in TransactionType]


def _svc() -> TransactionService:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return TransactionService(DataRepository(str(_DB_PATH)), ConfigRepository(str(_CONFIG_PATH)))


def _parse_decimal(ctx, param, value):
    if value is None:
        return None
    try:
        return Decimal(value)
    except Exception:
        raise click.BadParameter(f"数値ではありません: {value!r}")


@click.group()
def transaction():
    """取引の管理"""


@transaction.command("add")
@click.argument("plan_id")
@click.option("--type", "tx_type", required=True,
              type=click.Choice(_TYPE_CHOICES), prompt="取引種別",
              help="取引種別")
@click.option("--date", "tx_date", required=True, prompt="取引日 (YYYY-MM-DD)", help="取引日")
@click.option("--shares", default=None, callback=_parse_decimal, is_eager=False,
              help="取得/売却株数")
@click.option("--contribution", default=None, callback=_parse_decimal, is_eager=False,
              help="拠出金額")
@click.option("--incentive", default=None, callback=_parse_decimal, is_eager=False,
              help="奨励金額")
@click.option("--dividend", default=None, callback=_parse_decimal, is_eager=False,
              help="配当金額")
@click.option("--price", default=None, callback=_parse_decimal, is_eager=False,
              help="売却単価")
@click.option("--split-before", default=None, type=int, help="分割前株数")
@click.option("--split-after", default=None, type=int, help="分割後株数")
def transaction_add(plan_id, tx_type, tx_date, shares, contribution, incentive,
                    dividend, price, split_before, split_after):
    """取引を追加する"""
    try:
        d = date.fromisoformat(tx_date)
    except ValueError:
        raise click.BadParameter(f"日付形式が正しくありません: {tx_date!r}")
    tt = TransactionType(tx_type)
    kwargs = {}
    if shares is not None:
        kwargs["shares_quantity"] = shares
    if contribution is not None:
        kwargs["contribution_amount"] = contribution
    if incentive is not None:
        kwargs["incentive_amount"] = incentive
    if dividend is not None:
        kwargs["dividend_amount"] = dividend
    if price is not None:
        kwargs["sale_price_per_share"] = price
    if split_before is not None:
        kwargs["split_ratio_before"] = split_before
    if split_after is not None:
        kwargs["split_ratio_after"] = split_after
    try:
        tx = _svc().add_transaction(plan_id, tt, d, **kwargs)
    except (ValueError, Exception) as e:
        raise click.ClickException(str(e))
    click.echo(f"取引を追加しました: {tx.transaction_id}")
    click.echo(f"  種別: {tx.transaction_type.value}  日付: {tx.transaction_date}")
    click.echo(f"  保有株数: {tx.shares_held_after}  平均取得単価(奨励込): {tx.avg_cost_with}  (拠出のみ): {tx.avg_cost_without}")


@transaction.command("list")
@click.argument("plan_id")
def transaction_list(plan_id):
    """取引一覧を表示する"""
    try:
        txs = _svc().list_transactions(plan_id)
    except Exception as e:
        raise click.ClickException(str(e))
    if not txs:
        click.echo("取引が登録されていません。")
        return
    header = f"{'ID':36}  {'日付':<12}  {'種別':<25}  {'株数':>10}  {'平均(込)':>10}  {'平均(除)':>10}  {'損益(込)':>10}"
    click.echo(header)
    click.echo("-" * 130)
    for tx in txs:
        gain = str(tx.realized_gain_loss_with) if tx.realized_gain_loss_with is not None else "-"
        qty = str(tx.shares_quantity) if tx.shares_quantity is not None else "-"
        click.echo(
            f"{tx.transaction_id}  {tx.transaction_date}  {tx.transaction_type.value:<25}  "
            f"{qty:>10}  {tx.avg_cost_with:>10}  {tx.avg_cost_without:>10}  {gain:>10}"
        )


@transaction.command("edit")
@click.argument("transaction_id")
@click.option("--date", "tx_date", default=None, help="取引日 (YYYY-MM-DD)")
@click.option("--shares", default=None, callback=_parse_decimal, is_eager=False, help="株数")
@click.option("--contribution", default=None, callback=_parse_decimal, is_eager=False, help="拠出金額")
@click.option("--incentive", default=None, callback=_parse_decimal, is_eager=False, help="奨励金額")
@click.option("--dividend", default=None, callback=_parse_decimal, is_eager=False, help="配当金額")
@click.option("--price", default=None, callback=_parse_decimal, is_eager=False, help="売却単価")
@click.option("--split-before", default=None, type=int, help="分割前株数")
@click.option("--split-after", default=None, type=int, help="分割後株数")
def transaction_edit(transaction_id, tx_date, shares, contribution, incentive,
                     dividend, price, split_before, split_after):
    """取引を編集する（後続取引を自動再計算）"""
    kwargs = {}
    if tx_date is not None:
        try:
            kwargs["transaction_date"] = date.fromisoformat(tx_date)
        except ValueError:
            raise click.BadParameter(f"日付形式が正しくありません: {tx_date!r}")
    if shares is not None:
        kwargs["shares_quantity"] = shares
    if contribution is not None:
        kwargs["contribution_amount"] = contribution
    if incentive is not None:
        kwargs["incentive_amount"] = incentive
    if dividend is not None:
        kwargs["dividend_amount"] = dividend
    if price is not None:
        kwargs["sale_price_per_share"] = price
    if split_before is not None:
        kwargs["split_ratio_before"] = split_before
    if split_after is not None:
        kwargs["split_ratio_after"] = split_after
    if not kwargs:
        click.echo("変更する項目がありません。")
        return
    try:
        tx = _svc().edit_transaction(transaction_id, **kwargs)
    except ValueError as e:
        raise click.ClickException(str(e))
    click.echo(f"取引を更新しました: {tx.transaction_id}")
    click.echo(f"  保有株数: {tx.shares_held_after}  平均取得単価(奨励込): {tx.avg_cost_with}")


@transaction.command("delete")
@click.argument("transaction_id")
@click.confirmation_option(prompt="この取引を削除してよいですか？")
def transaction_delete(transaction_id):
    """取引を削除する（後続取引を自動再計算）"""
    try:
        _svc().delete_transaction(transaction_id)
    except ValueError as e:
        raise click.ClickException(str(e))
    click.echo(f"取引を削除しました: {transaction_id}")
