"""每日业务流水写入、查询与软删除。"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.daily_flow_report import DailyFlowReport, SalaryAccrual
from app.models.member import Member
from app.models.venue import Venue
from app.schemas.flow import DailyFlowCreate, DailyFlowListResponse, DailyFlowResponse
from app.services.flow_calculation_service import validate_profit_loss
from app.services.salary_rule_service import calculate_salary, list_games


class DuplicateFlowError(ValueError):
    """同一成员重复提交相同业务流水。"""


def _to_response(report: DailyFlowReport) -> DailyFlowResponse:
    accrual = report.salary_accrual
    return DailyFlowResponse(
        id=report.id,
        business_date=report.business_date,
        member_id=report.member_id,
        member_name=report.member.name,
        venue_id=report.venue_id,
        venue_name=report.venue.name,
        rebate_rate=report.venue.rebate_rate,
        game=report.game,
        card_number=report.card_number,
        principal=report.principal,
        chip_code=report.chip_code,
        loss_rebate=report.loss_rebate,
        profit_loss=report.profit_loss,
        salary_amount=accrual.salary_amount,
        salary_rule_description=accrual.rule_description,
        remark=report.remark,
        created_at=report.created_at,
        updated_at=report.updated_at,
    )


async def _load_report(session: AsyncSession, report_id: uuid.UUID) -> DailyFlowReport:
    stmt = (
        select(DailyFlowReport)
        .options(
            selectinload(DailyFlowReport.member),
            selectinload(DailyFlowReport.venue),
            selectinload(DailyFlowReport.salary_accrual),
        )
        .where(DailyFlowReport.id == report_id)
    )
    return (await session.execute(stmt)).scalar_one()


async def create_report(session: AsyncSession, data: DailyFlowCreate) -> DailyFlowResponse:
    """校验成员填报内容，写入流水并固化工资计提。"""

    validate_profit_loss(data.principal, data.chip_code, data.loss_rebate, data.profit_loss)
    member = await session.get(Member, data.member_id)
    if member is None or not member.is_active:
        raise LookupError(f"成员 {data.member_id} 不存在或已停用。")
    venue = await session.get(Venue, data.venue_id)
    if venue is None or not venue.is_active:
        raise LookupError(f"场子 {data.venue_id} 不存在或已停用。")
    if data.game not in list_games():
        raise ValueError(f"游戏 {data.game} 不在固定游戏列表中。")

    duplicate = await session.scalar(
        select(func.count())
        .select_from(DailyFlowReport)
        .where(
            DailyFlowReport.member_id == data.member_id,
            DailyFlowReport.business_date == data.business_date,
            DailyFlowReport.venue_id == data.venue_id,
            DailyFlowReport.profit_loss == data.profit_loss,
            DailyFlowReport.is_deleted.is_(False),
        )
    )
    if duplicate:
        raise DuplicateFlowError("重复上报：同一成员、业务日期、场子和赢亏的流水已存在。")

    salary = calculate_salary(venue.rebate_rate, data.game, data.profit_loss)
    report = DailyFlowReport(**data.model_dump())
    report.salary_accrual = SalaryAccrual(
        rebate_rate=venue.rebate_rate,
        salary_amount=salary.salary_amount,
        rule_description=salary.rule_description,
        rule_snapshot=salary.rule_snapshot,
    )
    session.add(report)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateFlowError("重复上报：同一成员、业务日期、场子和赢亏的流水已存在。") from exc
    return _to_response(await _load_report(session, report.id))


async def list_reports(
    session: AsyncSession,
    member_id: Optional[uuid.UUID] = None,
    venue_id: Optional[uuid.UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = 1,
    limit: int = 20,
) -> DailyFlowListResponse:
    """分页返回有效每日流水。"""

    filters = [DailyFlowReport.is_deleted.is_(False)]
    if member_id:
        filters.append(DailyFlowReport.member_id == member_id)
    if venue_id:
        filters.append(DailyFlowReport.venue_id == venue_id)
    if start_date:
        filters.append(DailyFlowReport.business_date >= start_date)
    if end_date:
        filters.append(DailyFlowReport.business_date <= end_date)
    where = and_(*filters)
    limit = min(limit, 100)
    total = await session.scalar(select(func.count()).select_from(DailyFlowReport).where(where)) or 0
    rows = (
        await session.execute(
            select(DailyFlowReport)
            .options(
                selectinload(DailyFlowReport.member),
                selectinload(DailyFlowReport.venue),
                selectinload(DailyFlowReport.salary_accrual),
            )
            .where(where)
            .order_by(desc(DailyFlowReport.business_date), desc(DailyFlowReport.created_at))
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).scalars().all()
    return DailyFlowListResponse(
        items=[_to_response(row) for row in rows],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, -(-total // limit)),
    )


async def delete_report(session: AsyncSession, report_id: uuid.UUID) -> None:
    """软删除每日流水，月度工资汇总会自动排除该笔计提。"""

    report = await session.scalar(
        select(DailyFlowReport).where(
            DailyFlowReport.id == report_id,
            DailyFlowReport.is_deleted.is_(False),
        )
    )
    if report is None:
        raise LookupError(f"流水 {report_id} 不存在或已删除。")
    report.is_deleted = True
    await session.flush()
