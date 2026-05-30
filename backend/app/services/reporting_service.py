"""仪表盘聚合查询。"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.daily_flow_report import DailyFlowReport, SalaryAccrual
from app.models.member_expense import MemberExpense
from app.models.venue import Venue
from app.schemas.dashboard import DailyTrendItem, DailyTrendResponse, SummaryResponse, VenueBreakdownItem, VenueBreakdownResponse

_ZERO = Decimal("0")


async def get_summary(session: AsyncSession) -> SummaryResponse:
    """返回业务流水、垫付支出和工资计提汇总。"""

    total_profit_loss = Decimal(str(await session.scalar(
        select(func.coalesce(func.sum(DailyFlowReport.profit_loss), 0)).where(DailyFlowReport.is_deleted.is_(False))
    ) or 0))
    total_expense = Decimal(str(await session.scalar(
        select(func.coalesce(func.sum(MemberExpense.amount), 0)).where(MemberExpense.is_deleted.is_(False))
    ) or 0))
    total_salary = Decimal(str(await session.scalar(
        select(func.coalesce(func.sum(SalaryAccrual.salary_amount), 0))
        .join(DailyFlowReport, SalaryAccrual.daily_flow_report_id == DailyFlowReport.id)
        .where(DailyFlowReport.is_deleted.is_(False))
    ) or 0))
    unreimbursed = Decimal(str(await session.scalar(
        select(func.coalesce(func.sum(MemberExpense.amount), 0)).where(
            MemberExpense.is_deleted.is_(False),
            MemberExpense.reimbursed.is_(False),
        )
    ) or 0))
    flow_count = await session.scalar(
        select(func.count()).select_from(DailyFlowReport).where(DailyFlowReport.is_deleted.is_(False))
    ) or 0
    expense_count = await session.scalar(
        select(func.count()).select_from(MemberExpense).where(MemberExpense.is_deleted.is_(False))
    ) or 0
    return SummaryResponse(
        total_profit_loss=total_profit_loss,
        total_expense=total_expense,
        total_salary=total_salary,
        net_result=total_profit_loss - total_expense - total_salary,
        flow_count=flow_count,
        expense_count=expense_count,
        unreimbursed_expense=unreimbursed,
    )


async def get_daily_trend(session: AsyncSession, days: int = 30) -> DailyTrendResponse:
    """返回最近若干天的业务趋势。"""

    since = datetime.now(timezone.utc).date() - timedelta(days=days - 1)
    flow_rows = (
        await session.execute(
            select(
                DailyFlowReport.business_date,
                func.sum(DailyFlowReport.profit_loss),
                func.sum(SalaryAccrual.salary_amount),
            )
            .join(SalaryAccrual, SalaryAccrual.daily_flow_report_id == DailyFlowReport.id)
            .where(DailyFlowReport.business_date >= since, DailyFlowReport.is_deleted.is_(False))
            .group_by(DailyFlowReport.business_date)
        )
    ).all()
    expense_rows = (
        await session.execute(
            select(MemberExpense.business_date, func.sum(MemberExpense.amount))
            .where(MemberExpense.business_date >= since, MemberExpense.is_deleted.is_(False))
            .group_by(MemberExpense.business_date)
        )
    ).all()
    values: dict[date, dict[str, Decimal]] = {}
    for day, profit_loss, salary in flow_rows:
        values[day] = {
            "profit_loss": Decimal(str(profit_loss or 0)),
            "salary": Decimal(str(salary or 0)),
            "expense": _ZERO,
        }
    for day, expense in expense_rows:
        values.setdefault(day, {"profit_loss": _ZERO, "salary": _ZERO, "expense": _ZERO})
        values[day]["expense"] = Decimal(str(expense or 0))
    items = []
    for day in sorted(values):
        value = values[day]
        items.append(DailyTrendItem(
            date=str(day),
            profit_loss=value["profit_loss"],
            salary=value["salary"],
            expense=value["expense"],
            net=value["profit_loss"] - value["salary"] - value["expense"],
        ))
    return DailyTrendResponse(data=items, period_days=days)


async def get_venue_breakdown(session: AsyncSession) -> VenueBreakdownResponse:
    """按场子返回流水赢亏。"""

    rows = (
        await session.execute(
            select(Venue.name, func.sum(DailyFlowReport.profit_loss), func.count(DailyFlowReport.id))
            .join(DailyFlowReport, DailyFlowReport.venue_id == Venue.id)
            .where(DailyFlowReport.is_deleted.is_(False))
            .group_by(Venue.name)
            .order_by(func.sum(DailyFlowReport.profit_loss).desc())
        )
    ).all()
    return VenueBreakdownResponse(
        items=[
            VenueBreakdownItem(
                venue_name=name,
                profit_loss=Decimal(str(profit_loss or 0)),
                flow_count=flow_count,
            )
            for name, profit_loss, flow_count in rows
        ]
    )
