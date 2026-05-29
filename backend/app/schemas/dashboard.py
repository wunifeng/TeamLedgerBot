"""Pydantic schemas for Dashboard API responses."""
from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class SummaryResponse(BaseModel):
    total_income: Decimal = Field(default=Decimal("0"))
    total_expense: Decimal = Field(default=Decimal("0"))
    total_salary: Decimal = Field(default=Decimal("0"))
    net_profit: Decimal = Field(default=Decimal("0"))   # income - expense - salary
    transaction_count: int = 0
    income_count: int = 0
    expense_count: int = 0
    salary_count: int = 0


class DailyTrendItem(BaseModel):
    date: str          # YYYY-MM-DD
    income: Decimal = Decimal("0")
    expense: Decimal = Decimal("0")
    salary: Decimal = Decimal("0")
    net: Decimal = Decimal("0")


class MonthlyTrendItem(BaseModel):
    month: str         # YYYY-MM
    income: Decimal = Decimal("0")
    expense: Decimal = Decimal("0")
    salary: Decimal = Decimal("0")
    net: Decimal = Decimal("0")


class CategoryBreakdownItem(BaseModel):
    category_id: str
    category_name: str
    type: str
    total: Decimal
    count: int
    percentage: float = 0.0


class DailyTrendResponse(BaseModel):
    data: List[DailyTrendItem]
    period_days: int = 30


class MonthlyTrendResponse(BaseModel):
    data: List[MonthlyTrendItem]
    period_months: int = 12


class CategoryBreakdownResponse(BaseModel):
    income: List[CategoryBreakdownItem]
    expense: List[CategoryBreakdownItem]
