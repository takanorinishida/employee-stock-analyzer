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
@click.option("--name", required=True, prompt="会社名", help="会社名")
@click.option("--start", required=True, prompt="開始日 (YYYY-MM-DD)", help="開始日")
@click.option("--code", default=None, help="証券コード")
def plan_add(name: str, start: str, code: str):
    """持株会を追加する"""
    try:
        start_date = date.fromisoformat(start)
    except ValueError:
        raise click.BadParameter(f"日付形式が正しくありません: {start!r}")
    p = _svc().create_plan(name, start_date, code)
    click.echo(f"持株会を追加しました: {p.plan_id}")
    click.echo(f"  会社名: {p.company_name}")
    click.echo(f"  開始日: {p.start_date}")
    if p.stock_code:
        click.echo(f"  証券コード: {p.stock_code}")


@plan.command("list")
def plan_list():
    """持株会一覧を表示する"""
    plans = _svc().list_plans()
    if not plans:
        click.echo("持株会が登録されていません。")
        return
    click.echo(f"{'ID':36}  {'会社名':<20}  {'コード':<8}  {'開始日':<12}  {'状態'}")
    click.echo("-" * 90)
    for p in plans:
        status = "有効" if p.is_active else "無効"
        code = p.stock_code or "-"
        click.echo(f"{p.plan_id}  {p.company_name:<20}  {code:<8}  {p.start_date}  {status}")


@plan.command("edit")
@click.argument("plan_id")
@click.option("--name", default=None, help="会社名")
@click.option("--code", default=None, help="証券コード")
@click.option("--start", default=None, help="開始日 (YYYY-MM-DD)")
@click.option("--end", default=None, help="終了日 (YYYY-MM-DD)")
@click.option("--active/--inactive", default=None, help="有効/無効")
def plan_edit(plan_id: str, name, code, start, end, active):
    """持株会を編集する"""
    kwargs = {}
    if name is not None:
        kwargs["company_name"] = name
    if code is not None:
        kwargs["stock_code"] = code
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
