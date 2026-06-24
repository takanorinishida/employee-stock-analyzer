from datetime import date
from pathlib import Path

import click

from infrastructure.data_repository import DataRepository
from service.plan_service import PlanService

_DB_PATH = Path.home() / ".stock-analyzer" / "data.db"


def _svc() -> PlanService:
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return PlanService(DataRepository(str(_DB_PATH)))


@click.group()
def plan():
    """持株会の管理"""


@plan.command("add")
@click.option("--id", "plan_id", required=True, prompt="プランID", help="プランID（推奨16文字以下）")
@click.option("--name", required=True, prompt="会社名", help="会社名")
@click.option("--start", required=True, prompt="開始日 (YYYY-MM-DD)", help="開始日")
@click.option("--ticker", default=None, help="ティッカー (例: 7203.T, AAPL)")
def plan_add(plan_id: str, name: str, start: str, ticker: str):
    """持株会を追加する"""
    if len(plan_id) > 16:
        click.echo(f"警告: プランIDは16文字以内を推奨します（現在: {len(plan_id)}文字）", err=True)
    try:
        start_date = date.fromisoformat(start)
    except ValueError:
        raise click.BadParameter(f"日付形式が正しくありません: {start!r}")
    try:
        p = _svc().create_plan(plan_id, name, start_date, ticker)
    except ValueError as e:
        raise click.ClickException(str(e))
    click.echo(f"持株会を追加しました: {p.plan_id}")
    click.echo(f"  会社名: {p.company_name}")
    click.echo(f"  開始日: {p.start_date}")
    if p.ticker:
        click.echo(f"  ティッカー: {p.ticker}")


@plan.command("list")
def plan_list():
    """持株会一覧を表示する"""
    plans = _svc().list_plans()
    if not plans:
        click.echo("持株会が登録されていません。")
        return
    id_width = max(4, max(len(p.plan_id) for p in plans))
    click.echo(f"{'ID':<{id_width}}  {'会社名':<20}  {'ティッカー':<12}  {'開始日':<12}  {'状態'}")
    click.echo("-" * (id_width + 60))
    for p in plans:
        status = "有効" if p.is_active else "無効"
        ticker = p.ticker or "-"
        click.echo(f"{p.plan_id:<{id_width}}  {p.company_name:<20}  {ticker:<12}  {p.start_date}  {status}")


@plan.command("edit")
@click.argument("plan_id")
@click.option("--name", default=None, help="会社名")
@click.option("--ticker", default=None, help="ティッカー (例: 7203.T, AAPL)")
@click.option("--start", default=None, help="開始日 (YYYY-MM-DD)")
@click.option("--end", default=None, help="終了日 (YYYY-MM-DD)")
@click.option("--active/--inactive", default=None, help="有効/無効")
def plan_edit(plan_id: str, name, ticker, start, end, active):
    """持株会を編集する"""
    kwargs = {}
    if name is not None:
        kwargs["company_name"] = name
    if ticker is not None:
        kwargs["ticker"] = ticker
    if start is not None:
        try:
            kwargs["start_date"] = date.fromisoformat(start)
        except ValueError:
            raise click.BadParameter(f"日付形式が正しくありません: {start!r}")
    if end is not None:
        try:
            kwargs["end_date"] = date.fromisoformat(end)
        except ValueError:
            raise click.BadParameter(f"日付形式が正しくありません: {end!r}")
    if active is not None:
        kwargs["is_active"] = active
    if not kwargs:
        click.echo("変更する項目がありません。")
        return
    try:
        p = _svc().update_plan(plan_id, **kwargs)
    except ValueError as e:
        raise click.ClickException(str(e))
    click.echo(f"持株会を更新しました: {p.plan_id}")
