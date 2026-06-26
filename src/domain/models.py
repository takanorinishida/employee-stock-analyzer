from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class TransactionType(Enum):
    CONTRIBUTION = "CONTRIBUTION"
    DIVIDEND_REINVESTMENT = "DIVIDEND_REINVESTMENT"
    SALE = "SALE"
    STOCK_SPLIT = "STOCK_SPLIT"
    REVERSE_SPLIT = "REVERSE_SPLIT"


@dataclass
class Plan:
    plan_id: str
    company_name: str
    start_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime
    ticker: Optional[str] = None
    end_date: Optional[date] = None


@dataclass
class Transaction:
    transaction_id: str
    plan_id: str
    transaction_type: TransactionType
    transaction_date: date
    avg_cost_with: Decimal
    avg_cost_without: Decimal
    shares_held_after: Decimal
    created_at: datetime
    updated_at: datetime
    shares_quantity: Optional[Decimal] = None
    contribution_amount: Optional[Decimal] = None
    incentive_amount: Optional[Decimal] = None
    dividend_amount: Optional[Decimal] = None
    sale_price_per_share: Optional[Decimal] = None
    split_ratio_before: Optional[int] = None
    split_ratio_after: Optional[int] = None
    realized_gain_loss_with: Optional[Decimal] = None
    realized_gain_loss_without: Optional[Decimal] = None
    carryover_amount: Optional[Decimal] = None
    employee_carryover_amount: Optional[Decimal] = None
