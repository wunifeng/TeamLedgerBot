"""业务仪表盘 API schema。"""
from decimal import Decimal
from typing import List

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    total_profit_loss: Decimal = Decimal("0")
    total_expense: Decimal = Decimal("0")
    total_salary: Decimal = Decimal("0")
    net_result: Decimal = Decimal("0")
    flow_count: int = 0
    expense_count: int = 0
    unreimbursed_expense: Decimal = Decimal("0")


class DailyTrendItem(BaseModel):
    date: str
    profit_loss: Decimal = Decimal("0")
    expense: Decimal = Decimal("0")
    salary: Decimal = Decimal("0")
    net: Decimal = Decimal("0")


class DailyTrendResponse(BaseModel):
    data: List[DailyTrendItem]
    period_days: int = 30


class VenueBreakdownItem(BaseModel):
    venue_name: str
    profit_loss: Decimal
    flow_count: int


class VenueBreakdownResponse(BaseModel):
    items: List[VenueBreakdownItem]
