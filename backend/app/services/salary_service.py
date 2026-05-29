"""薪资账期结算服务。"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.member import Member
from app.models.salary_settlement import SalarySettlement
from app.schemas.salary import (
    SalaryPaymentCreate,
    SalaryPaymentResponse,
    SalarySettlementCreate,
    SalarySettlementListResponse,
    SalarySettlementResponse,
)
from app.schemas.transaction import SalaryCreate
from app.services import transaction_service

_ZERO = Decimal("0")


def _paid_total(amount: Decimal, bonus: Optional[Decimal]) -> Decimal:
    return amount + (bonus or _ZERO)


def _status(payable: Decimal, paid: Decimal) -> str:
    if paid <= _ZERO:
        return "unpaid"
    if paid < payable:
        return "partial"
    return "paid"


def _to_response(settlement: SalarySettlement) -> SalarySettlementResponse:
    unpaid = max(_ZERO, settlement.payable_amount - settlement.paid_amount)
    return SalarySettlementResponse(
        id=settlement.id,
        member_id=settlement.member_id,
        member_name=settlement.member.name if settlement.member else "",
        period_start=settlement.period_start,
        period_end=settlement.period_end,
        payable_amount=settlement.payable_amount,
        paid_amount=settlement.paid_amount,
        unpaid_amount=unpaid,
        status=_status(settlement.payable_amount, settlement.paid_amount),
        remark=settlement.remark,
        created_at=settlement.created_at,
        updated_at=settlement.updated_at,
    )


async def _load_settlement(
    session: AsyncSession,
    settlement_id: uuid.UUID,
) -> SalarySettlement:
    stmt = (
        select(SalarySettlement)
        .options(selectinload(SalarySettlement.member))
        .where(SalarySettlement.id == settlement_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


async def list_settlements(
    session: AsyncSession,
    period_start: Optional[date] = None,
    period_end: Optional[date] = None,
    include_inactive: bool = True,
) -> SalarySettlementListResponse:
    filters = []
    if period_start:
        filters.append(SalarySettlement.period_start == period_start)
    if period_end:
        filters.append(SalarySettlement.period_end == period_end)

    stmt = (
        select(SalarySettlement)
        .options(selectinload(SalarySettlement.member))
        .join(Member, SalarySettlement.member_id == Member.id)
        .order_by(Member.name)
    )
    if filters:
        stmt = stmt.where(and_(*filters))
    if not include_inactive:
        stmt = stmt.where(Member.is_active.is_(True))

    rows = (await session.execute(stmt)).scalars().all()
    items = [_to_response(row) for row in rows]
    return SalarySettlementListResponse(
        items=items,
        total_payable=sum((item.payable_amount for item in items), _ZERO),
        total_paid=sum((item.paid_amount for item in items), _ZERO),
        total_unpaid=sum((item.unpaid_amount for item in items), _ZERO),
    )


async def create_or_update_settlement(
    session: AsyncSession,
    data: SalarySettlementCreate,
) -> SalarySettlementResponse:
    member = await session.get(Member, data.member_id)
    if member is None:
        raise LookupError(f"Member {data.member_id} not found.")

    stmt = select(SalarySettlement).where(
        SalarySettlement.member_id == data.member_id,
        SalarySettlement.period_start == data.period_start,
        SalarySettlement.period_end == data.period_end,
    )
    existing = (await session.execute(stmt)).scalar_one_or_none()
    if existing:
        if data.payable_amount < existing.paid_amount:
            raise ValueError("payable_amount cannot be less than already paid amount.")
        existing.payable_amount = data.payable_amount
        existing.remark = data.remark
        await session.flush()
        return _to_response(await _load_settlement(session, existing.id))

    settlement = SalarySettlement(
        member_id=data.member_id,
        period_start=data.period_start,
        period_end=data.period_end,
        payable_amount=data.payable_amount,
        paid_amount=_ZERO,
        remark=data.remark,
    )
    session.add(settlement)
    await session.flush()
    return _to_response(await _load_settlement(session, settlement.id))


async def pay_settlement(
    session: AsyncSession,
    settlement_id: uuid.UUID,
    data: SalaryPaymentCreate,
) -> SalaryPaymentResponse:
    settlement = await _load_settlement(session, settlement_id)
    pay_total = _paid_total(data.amount, data.bonus)
    unpaid = settlement.payable_amount - settlement.paid_amount
    if pay_total > unpaid:
        raise ValueError("payment amount cannot exceed unpaid amount.")

    tx, alerts = await transaction_service.create_salary(
        session,
        SalaryCreate(
            member_id=settlement.member_id,
            salary_amount=data.amount,
            bonus=data.bonus,
            remark=data.remark,
            timestamp=data.timestamp,
        ),
        salary_settlement_id=settlement.id,
    )
    settlement.paid_amount += pay_total
    await session.flush()
    refreshed = await _load_settlement(session, settlement.id)
    return SalaryPaymentResponse(
        settlement=_to_response(refreshed),
        transaction=tx,
        alerts=alerts,
    )
