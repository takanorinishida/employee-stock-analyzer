from datetime import date, datetime
from typing import Optional

from domain.models import Plan
from infrastructure.data_repository import DataRepository


class PlanService:
    def __init__(self, repo: DataRepository):
        self._repo = repo

    def create_plan(
        self,
        plan_id: str,
        company_name: str,
        start_date: date,
        ticker: Optional[str] = None,
    ) -> Plan:
        now = datetime.now()
        plan = Plan(
            plan_id=plan_id,
            company_name=company_name,
            ticker=ticker,
            start_date=start_date,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        try:
            self._repo.save_plan(plan)
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"プランID '{plan_id}' は既に使用されています")
            raise
        return plan

    def update_plan(
        self,
        plan_id: str,
        company_name: Optional[str] = None,
        ticker: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_active: Optional[bool] = None,
    ) -> Plan:
        plan = self._get_or_raise(plan_id)
        if company_name is not None:
            plan.company_name = company_name
        if ticker is not None:
            plan.ticker = ticker
        if start_date is not None:
            plan.start_date = start_date
        if end_date is not None:
            plan.end_date = end_date
        if is_active is not None:
            plan.is_active = is_active
        plan.updated_at = datetime.now()
        self._repo.save_plan(plan)
        return plan

    def list_plans(self) -> list[Plan]:
        return self._repo.list_plans()

    def get_plan(self, plan_id: str) -> Optional[Plan]:
        return self._repo.get_plan(plan_id)

    def _get_or_raise(self, plan_id: str) -> Plan:
        plan = self._repo.get_plan(plan_id)
        if plan is None:
            raise ValueError(f"持株会が見つかりません: {plan_id}")
        return plan
