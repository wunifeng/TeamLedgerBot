"""工资月结与实际发放服务。"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.daily_flow_report import DailyFlowReport, SalaryAccrual
from app.models.member import Member
from app.models.salary_settlement import SalaryPayment, SalarySettlement
from app.schemas.salary import (
    SalaryPaymentCreate,
    SalaryPaymentItem,
    SalaryPaymentResponse,
    SalaryPaymentVoidCreate,
    SalarySettlementListResponse,
    SalarySettlementResponse,
)

_ZERO = Decimal("0")


def _status(payable: Decimal, paid: Decimal) -> str:
    if paid <= _ZERO:
        return "unpaid"
    if paid < payable:
        return "partial"
    return "paid"


async def _payable(
    session: AsyncSession,
    member_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> Decimal:
    amount = await session.scalar(
        select(func.coalesce(func.sum(SalaryAccrual.salary_amount), 0))
        .join(DailyFlowReport, SalaryAccrual.daily_flow_report_id == DailyFlowReport.id)
        .where(
            DailyFlowReport.member_id == member_id,
            DailyFlowReport.business_date >= period_start,
            DailyFlowReport.business_date <= period_end,
            DailyFlowReport.is_deleted.is_(False),
        )
    )
    return Decimal(str(amount or 0))


async def _paid(session: AsyncSession, settlement_id: uuid.UUID) -> Decimal:
    amount = await session.scalar(
        select(func.coalesce(func.sum(SalaryPayment.amount), 0)).where(
            SalaryPayment.settlement_id == settlement_id,
            SalaryPayment.voided_at.is_(None),
        )
    )
    return Decimal(str(amount or 0))


async def _payment_items(session: AsyncSession, settlement_id: uuid.UUID) -> list[SalaryPaymentItem]:
    rows = (
        await session.execute(
            select(SalaryPayment)
            .where(SalaryPayment.settlement_id == settlement_id)
            .order_by(SalaryPayment.paid_at.desc(), SalaryPayment.created_at.desc())
        )
    ).scalars().all()
    return [
        SalaryPaymentItem(
            id=row.id,
            settlement_id=row.settlement_id,
            amount=row.amount,
            remark=row.remark,
            paid_at=row.paid_at,
            voided_at=row.voided_at,
            void_reason=row.void_reason,
        )
        for row in rows
    ]


async def _get_or_create_settlement(
    session: AsyncSession,
    member_id: uuid.UUID,
    period_start: date,
    period_end: date,
) -> SalarySettlement:
    settlement = await session.scalar(
        select(SalarySettlement)
        .options(selectinload(SalarySettlement.member))
        .where(
            SalarySettlement.member_id == member_id,
            SalarySettlement.period_start == period_start,
            SalarySettlement.period_end == period_end,
        )
    )
    if settlement:
        return settlement
    settlement = SalarySettlement(
        member_id=member_id,
        period_start=period_start,
        period_end=period_end,
    )
    session.add(settlement)
    await session.flush()
    return (
        await session.execute(
            select(SalarySettlement)
            .options(selectinload(SalarySettlement.member))
            .where(SalarySettlement.id == settlement.id)
        )
    ).scalar_one()


async def _to_response(
    session: AsyncSession,
    settlement: SalarySettlement,
) -> SalarySettlementResponse:
    payable = await _payable(session, settlement.member_id, settlement.period_start, settlement.period_end)
    paid = await _paid(session, settlement.id)
    unpaid = max(_ZERO, payable - paid)
    payments = await _payment_items(session, settlement.id)
    return SalarySettlementResponse(
        id=settlement.id,
        member_id=settlement.member_id,
        member_name=settlement.member.name,
        period_start=settlement.period_start,
        period_end=settlement.period_end,
        payable_amount=payable,
        paid_amount=paid,
        unpaid_amount=unpaid,
        status=_status(payable, paid),
        remark=settlement.remark,
        payments=payments,
        created_at=settlement.created_at,
        updated_at=settlement.updated_at,
    )


async def list_settlements(
    session: AsyncSession,
    period_start: date,
    period_end: date,
    include_inactive: bool = True,
) -> SalarySettlementListResponse:
    """返回指定月度账期的成员工资汇总。"""

    stmt = select(Member).order_by(Member.name)
    if not include_inactive:
        stmt = stmt.where(Member.is_active.is_(True))
    members = (await session.execute(stmt)).scalars().all()
    settlements = [
        await _get_or_create_settlement(session, member.id, period_start, period_end)
        for member in members
    ]
    items = [await _to_response(session, settlement) for settlement in settlements]
    return SalarySettlementListResponse(
        items=items,
        total_payable=sum((item.payable_amount for item in items), _ZERO),
        total_paid=sum((item.paid_amount for item in items), _ZERO),
        total_unpaid=sum((item.unpaid_amount for item in items), _ZERO),
    )


async def pay_settlement(
    session: AsyncSession,
    settlement_id: uuid.UUID,
    data: SalaryPaymentCreate,
) -> SalaryPaymentResponse:
    """登记实际工资发放，禁止超额支付。"""

    settlement = (
        await session.execute(
            select(SalarySettlement)
            .options(selectinload(SalarySettlement.member))
            .where(SalarySettlement.id == settlement_id)
        )
    ).scalar_one_or_none()
    if settlement is None:
        raise LookupError(f"工资账期 {settlement_id} 不存在。")
    current = await _to_response(session, settlement)
    if data.amount > current.unpaid_amount:
        raise ValueError("发放金额不能超过未付工资。")
    payment = SalaryPayment(
        settlement_id=settlement.id,
        amount=data.amount,
        remark=data.remark,
    )
    session.add(payment)
    await session.flush()
    settlement_response = await _to_response(session, settlement)
    payment_item = next(
        item for item in settlement_response.payments
        if item.id == payment.id
    )
    return SalaryPaymentResponse(
        settlement=settlement_response,
        payment=payment_item,
    )


async def void_payment(
    session: AsyncSession,
    payment_id: uuid.UUID,
    data: SalaryPaymentVoidCreate,
    operator_id: uuid.UUID,
) -> SalaryPaymentResponse:
    """作废错误登记的工资发放记录，并保留原始记录。"""

    payment = (
        await session.execute(
            select(SalaryPayment)
            .options(
                selectinload(SalaryPayment.settlement).selectinload(SalarySettlement.member)
            )
            .where(SalaryPayment.id == payment_id)
        )
    ).scalar_one_or_none()
    if payment is None:
        raise LookupError(f"工资发放记录 {payment_id} 不存在。")
    if payment.voided_at is not None:
        raise ValueError("工资发放记录已经作废。")

    payment.voided_at = datetime.now(timezone.utc)
    payment.void_reason = data.reason
    payment.voided_by_member_id = operator_id
    await session.flush()

    settlement_response = await _to_response(session, payment.settlement)
    payment_item = next(
        item for item in settlement_response.payments
        if item.id == payment.id
    )
    return SalaryPaymentResponse(
        settlement=settlement_response,
        payment=payment_item,
    )
