"""每日业务流水写入、查询、编辑、软删除与变更日志。"""
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.daily_flow_report import DailyFlowReport, FlowChangeLog, SalaryAccrual
from app.models.member import Member
from app.models.venue import Venue
from app.schemas.flow import (
    DailyFlowCreate,
    DailyFlowListResponse,
    DailyFlowResponse,
    DailyFlowUpdate,
    FlowChangeLogResponse,
)
from app.services.flow_calculation_service import validate_profit_loss
from app.services.salary_rule_service import calculate_salary, list_games


class DuplicateFlowError(ValueError):
    """同一成员重复提交相同业务流水。"""


def _report_snapshot(report: DailyFlowReport) -> dict:
    """将流水核心字段序列化为 JSON 快照（用于变更日志）。"""
    return {
        "principal": str(report.principal),
        "chip_code": str(report.chip_code),
        "loss_rebate": str(report.loss_rebate),
        "profit_loss": str(report.profit_loss),
        "remark": report.remark,
        "salary_amount": str(report.salary_accrual.salary_amount) if report.salary_accrual else None,
    }


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


def _write_change_log(
    session: AsyncSession,
    report: DailyFlowReport,
    change_type: str,
    operator: Member,
    before_data: Optional[dict] = None,
    after_data: Optional[dict] = None,
) -> None:
    """写入流水变更日志（同步，不提交 session）。"""
    log = FlowChangeLog(
        flow_id=report.id,
        operator_id=operator.id,
        operator_name=operator.name,
        change_type=change_type,
        before_data=before_data,
        after_data=after_data,
    )
    session.add(log)


async def create_report(
    session: AsyncSession, data: DailyFlowCreate, operator: Member
) -> DailyFlowResponse:
    """校验成员填报内容，写入流水并固化工资计提，记录创建日志。"""

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

    # 写创建日志（需要 flush 之后 report.id 才有值）
    loaded = await _load_report(session, report.id)
    _write_change_log(
        session,
        loaded,
        change_type="create",
        operator=operator,
        before_data=None,
        after_data=_report_snapshot(loaded),
    )
    await session.flush()
    return _to_response(loaded)


async def update_report(
    session: AsyncSession,
    report_id: uuid.UUID,
    data: DailyFlowUpdate,
    operator: Member,
) -> DailyFlowResponse:
    """修改流水字段，重算工资，记录变更日志。"""

    report = await session.scalar(
        select(DailyFlowReport)
        .options(
            selectinload(DailyFlowReport.member),
            selectinload(DailyFlowReport.venue),
            selectinload(DailyFlowReport.salary_accrual),
        )
        .where(DailyFlowReport.id == report_id, DailyFlowReport.is_deleted.is_(False))
    )
    if report is None:
        raise LookupError(f"流水 {report_id} 不存在或已删除。")

    # 权限检查：管理员可修改所有人，普通成员只能修改自己的
    from fastapi import HTTPException, status as http_status
    if not operator.is_admin and operator.id != report.member_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="无权限：只能修改自己的流水",
        )

    # 保存修改前快照
    before = _report_snapshot(report)

    # 合并更新字段
    update_dict = data.model_dump(exclude_unset=True)
    new_principal = Decimal(str(update_dict.get("principal", report.principal)))
    new_chip_code = Decimal(str(update_dict.get("chip_code", report.chip_code)))
    new_loss_rebate = Decimal(str(update_dict.get("loss_rebate", report.loss_rebate)))
    new_profit_loss = Decimal(str(update_dict.get("profit_loss", report.profit_loss)))

    # 校验金额一致性（如果任意金额字段被修改）
    amount_fields = {"principal", "chip_code", "loss_rebate", "profit_loss"}
    if amount_fields & set(update_dict.keys()):
        validate_profit_loss(new_principal, new_chip_code, new_loss_rebate, new_profit_loss)

    # 为了规避唯一索引，先临时标记 is_deleted=True
    report.is_deleted = True
    await session.flush()

    # 更新字段
    for field, value in update_dict.items():
        setattr(report, field, value)
    report.is_deleted = False

    # 删除旧的 SalaryAccrual，重新计算
    old_accrual = report.salary_accrual
    if old_accrual is not None:
        await session.delete(old_accrual)
        await session.flush()

    salary = calculate_salary(report.venue.rebate_rate, report.game, new_profit_loss)
    new_accrual = SalaryAccrual(
        daily_flow_report_id=report.id,
        rebate_rate=report.venue.rebate_rate,
        salary_amount=salary.salary_amount,
        rule_description=salary.rule_description,
        rule_snapshot=salary.rule_snapshot,
    )
    session.add(new_accrual)

    try:
        await session.flush()
    except IntegrityError as exc:
        raise DuplicateFlowError("修改后的数据与已有流水重复，请检查字段。") from exc

    # 重新加载以获取最新快照
    loaded = await _load_report(session, report.id)
    after = _report_snapshot(loaded)

    _write_change_log(
        session, loaded, change_type="update", operator=operator,
        before_data=before, after_data=after,
    )
    await session.flush()
    return _to_response(loaded)


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


async def delete_report(
    session: AsyncSession, report_id: uuid.UUID, operator: Member
) -> dict:
    """软删除每日流水，记录删除日志，返回删除前快照（用于 Telegram 通知）。"""

    report = await session.scalar(
        select(DailyFlowReport)
        .options(
            selectinload(DailyFlowReport.member),
            selectinload(DailyFlowReport.venue),
            selectinload(DailyFlowReport.salary_accrual),
        )
        .where(
            DailyFlowReport.id == report_id,
            DailyFlowReport.is_deleted.is_(False),
        )
    )
    if report is None:
        raise LookupError(f"流水 {report_id} 不存在或已删除。")

    # 权限检查
    from fastapi import HTTPException, status as http_status
    if not operator.is_admin and operator.id != report.member_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="无权限：只能删除自己的流水",
        )

    before = _report_snapshot(report)
    member_name = report.member.name

    _write_change_log(
        session, report, change_type="delete", operator=operator,
        before_data=before, after_data=None,
    )
    report.is_deleted = True
    await session.flush()

    return {
        "member_name": member_name,
        "business_date": str(report.business_date),
        "venue_name": report.venue.name,
        "profit_loss": str(report.profit_loss),
        "salary_amount": before.get("salary_amount"),
    }


async def get_flow_history(
    session: AsyncSession, report_id: uuid.UUID
) -> List[FlowChangeLogResponse]:
    """返回某条流水的完整变更历史，按时间升序。"""
    rows = (
        await session.execute(
            select(FlowChangeLog)
            .where(FlowChangeLog.flow_id == report_id)
            .order_by(FlowChangeLog.changed_at)
        )
    ).scalars().all()
    return [
        FlowChangeLogResponse(
            id=row.id,
            flow_id=row.flow_id,
            changed_at=row.changed_at,
            operator_name=row.operator_name,
            change_type=row.change_type,
            before_data=row.before_data,
            after_data=row.after_data,
        )
        for row in rows
    ]
