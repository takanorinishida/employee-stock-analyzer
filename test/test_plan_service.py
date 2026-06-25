"""PlanService のユニットテスト"""
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from infrastructure.data_repository import DataRepository
from service.plan_service import PlanService


def _svc(tmp_path) -> PlanService:
    return PlanService(DataRepository(str(tmp_path / "test.db")))


class TestCreatePlanId:
    @pytest.mark.parametrize("plan_id", [
        "toyota",
        "my-plan",
        "my_plan",
        "7203.T",
        "AAPL",
        "plan123",
    ])
    def test_valid_plan_id(self, tmp_path, plan_id):
        plan = _svc(tmp_path).create_plan(plan_id, "テスト会社", date(2024, 1, 1))
        assert plan.plan_id == plan_id

    @pytest.mark.parametrize("plan_id", [
        "my plan",
        "my@plan",
        "会社A",
        "plan!",
        "plan/id",
    ])
    def test_invalid_plan_id(self, tmp_path, plan_id):
        with pytest.raises(ValueError, match="使用できない文字"):
            _svc(tmp_path).create_plan(plan_id, "テスト会社", date(2024, 1, 1))

    def test_duplicate_plan_id(self, tmp_path):
        svc = _svc(tmp_path)
        svc.create_plan("toyota", "テスト会社", date(2024, 1, 1))
        with pytest.raises(ValueError, match="既に使用されています"):
            svc.create_plan("toyota", "別の会社", date(2024, 1, 1))
