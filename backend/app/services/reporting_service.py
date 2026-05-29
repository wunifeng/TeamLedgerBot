"""Reporting Service — aggregations and chart data for Dashboard endpoints."""
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, case, cast, func, select
from sqlalchemy.dialects.postgresql import DATE
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.models.transaction import Transaction
from app.schemas.dashboard import (
    CategoryBreakdownItem,
    CategoryBreakdownResponse,
    DailyTrendItem,
    DailyTrendResponse,
    MonthlyTrendItem,
    MonthlyTrendResponse,
    SummaryResponse,
)

logger = logging.getLogger(__name__)

_ZERO = Decimal("0")


def _salary_total_expr():
    return Transaction.amount + func.coalesce(Transaction.bonus, 0)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _active_tx_base(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """Return base WHERE conditions for non-deleted transactions within date range."""
    conditions = [Transaction.is_deleted.is_(False)]
    if start_date:
        conditions.append(Transaction.created_at >= start_date)
    if end_date:
        conditions.append(Transaction.created_at <= end_date)
    return and_(*conditions)


# ── Summary ────────────────────────────────────────────────────────────────────

async def get_summary(
    session: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> SummaryResponse:
    """Return aggregate totals and counts, optionally filtered by date range."""
    where = _active_tx_base(start_date, end_date)
    salary_total = _salary_total_expr()

    stmt = select(
        func.sum(
            case((Transaction.type == "income", Transaction.amount), else_=0)
        ).label("total_income"),
        func.sum(
            case((Transaction.type == "expense", Transaction.amount), else_=0)
        ).label("total_expense"),
        func.sum(
            case((Transaction.type == "salary", salary_total), else_=0)
        ).label("total_salary"),
        func.count().label("transaction_count"),
        func.sum(
            case((Transaction.type == "income", 1), else_=0)
        ).label("income_count"),
        func.sum(
            case((Transaction.type == "expense", 1), else_=0)
        ).label("expense_count"),
        func.sum(
            case((Transaction.type == "salary", 1), else_=0)
        ).label("salary_count"),
    ).where(where)

    row = (await session.execute(stmt)).one()

    total_income = Decimal(str(row.total_income or 0))
    total_expense = Decimal(str(row.total_expense or 0))
    total_salary = Decimal(str(row.total_salary or 0))

    return SummaryResponse(
        total_income=total_income,
        total_expense=total_expense,
        total_salary=total_salary,
        net_profit=total_income - total_expense - total_salary,
        transaction_count=row.transaction_count or 0,
        income_count=row.income_count or 0,
        expense_count=row.expense_count or 0,
        salary_count=row.salary_count or 0,
    )


# ── Daily trend ────────────────────────────────────────────────────────────────

async def get_daily_trend(
    session: AsyncSession,
    days: int = 30,
) -> DailyTrendResponse:
    """Return per-day income/expense totals for the last `days` days."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    where = _active_tx_base(start_date=since)
    salary_total = _salary_total_expr()

    # Cast created_at to DATE in the DB's UTC representation
    date_col = cast(Transaction.created_at, DATE).label("day")

    stmt = (
        select(
            date_col,
            func.sum(
                case((Transaction.type == "income", Transaction.amount), else_=0)
            ).label("income"),
            func.sum(
                case((Transaction.type == "expense", Transaction.amount), else_=0)
            ).label("expense"),
            func.sum(
                case((Transaction.type == "salary", salary_total), else_=0)
            ).label("salary"),
        )
        .where(where)
        .group_by(date_col)
        .order_by(date_col)
    )

    rows = (await session.execute(stmt)).all()
    data = [
        (
            Decimal(str(row.income or 0)),
            Decimal(str(row.expense or 0)),
            Decimal(str(row.salary or 0)),
            row.day,
        )
        for row in rows
    ]
    return DailyTrendResponse(
        data=[
            DailyTrendItem(
                date=str(day),
                income=income,
                expense=expense,
                salary=salary,
                net=income - expense - salary,
            )
            for income, expense, salary, day in data
        ],
        period_days=days,
    )


# ── Monthly trend ──────────────────────────────────────────────────────────────

async def get_monthly_trend(
    session: AsyncSession,
    months: int = 12,
) -> MonthlyTrendResponse:
    """Return per-month income/expense/salary totals for the last `months` months."""
    since = datetime.now(timezone.utc) - timedelta(days=months * 31)
    where = _active_tx_base(start_date=since)
    salary_total = _salary_total_expr()

    # Format as YYYY-MM string
    month_col = func.to_char(Transaction.created_at, "YYYY-MM").label("month")

    stmt = (
        select(
            month_col,
            func.sum(
                case((Transaction.type == "income", Transaction.amount), else_=0)
            ).label("income"),
            func.sum(
                case((Transaction.type == "expense", Transaction.amount), else_=0)
            ).label("expense"),
            func.sum(
                case((Transaction.type == "salary", salary_total), else_=0)
            ).label("salary"),
        )
        .where(where)
        .group_by(month_col)
        .order_by(month_col)
    )

    rows = (await session.execute(stmt)).all()
    data = [
        MonthlyTrendItem(
            month=row.month,
            income=Decimal(str(row.income or 0)),
            expense=Decimal(str(row.expense or 0)),
            salary=Decimal(str(row.salary or 0)),
            net=(
                Decimal(str(row.income or 0))
                - Decimal(str(row.expense or 0))
                - Decimal(str(row.salary or 0))
            ),
        )
        for row in rows
    ]
    return MonthlyTrendResponse(data=data, period_months=months)


# ── Category breakdown ─────────────────────────────────────────────────────────

async def get_category_breakdown(
    session: AsyncSession,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> CategoryBreakdownResponse:
    """Return per-category totals and percentages for income and expense."""
    where = _active_tx_base(start_date, end_date)
    # Only income and expense have categories
    where = and_(where, Transaction.type.in_(["income", "expense"]))

    stmt = (
        select(
            Transaction.category_id,
            func.coalesce(Category.name, "Uncategorized").label("category_name"),
            Transaction.type,
            func.sum(Transaction.amount).label("total"),
            func.count().label("count"),
        )
        .outerjoin(Category, Transaction.category_id == Category.id)
        .where(where)
        .group_by(Transaction.category_id, Category.name, Transaction.type)
        .order_by(func.sum(Transaction.amount).desc())
    )

    rows = (await session.execute(stmt)).all()

    # Separate by type and compute percentages
    income_rows = [r for r in rows if r.type == "income"]
    expense_rows = [r for r in rows if r.type == "expense"]

    income_total = sum(Decimal(str(r.total or 0)) for r in income_rows) or _ZERO
    expense_total = sum(Decimal(str(r.total or 0)) for r in expense_rows) or _ZERO

    def _to_item(row, grand_total: Decimal) -> CategoryBreakdownItem:
        total = Decimal(str(row.total or 0))
        pct = float(total / grand_total * 100) if grand_total else 0.0
        return CategoryBreakdownItem(
            category_id=str(row.category_id) if row.category_id else "uncategorized",
            category_name=row.category_name,
            type=row.type,
            total=total,
            count=row.count,
            percentage=round(pct, 2),
        )

    return CategoryBreakdownResponse(
        income=[_to_item(r, income_total) for r in income_rows],
        expense=[_to_item(r, expense_total) for r in expense_rows],
    )
