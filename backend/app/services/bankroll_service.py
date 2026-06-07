"""成员 bankroll 余额计算、登记与作废服务。"""
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Iterable, Optional

from fastapi import HTTPException, status as http_status
from sqlalchemy import and_, case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.bankroll_entry import BankrollEntry
from app.models.member import Member
from app.schemas.bankroll import (
    BankrollEntryCreate,
    BankrollEntryListResponse,
    BankrollEntryResponse,
    BankrollEntryVoidCreate,
    BankrollMemberBalance,
    BankrollSummaryResponse,
)

_ZERO = Decimal("0")
_INCREASE_TYPES = {"initial", "top_up"}
_VALID_TYPES = {"initial", "top_up", "return", "adjustment"}
_VALID_DIRECTIONS = {"increase", "decrease"}


def _has_text(value: Optional[str]) -> bool:
    return bool(value and value.strip())


def calculate_signed_amount(
    entry_type: str,
    amount: Decimal,
    adjustment_direction: Optional[str] = None,
) -> Decimal:
    """根据 bankroll 变动类型计算对成员余额的影响。"""

    if entry_type in _INCREASE_TYPES:
        return amount
    if entry_type == "return":
        return -amount
    if entry_type == "adjustment":
        if adjustment_direction == "increase":
            return amount
        if adjustment_direction == "decrease":
            return -amount
    raise ValueError("bankroll 变动类型或调整方向无效。")


def calculate_balance_from_entries(
    entries: Iterable[tuple[str, Decimal, Optional[str]]],
) -> Decimal:
    """按有效 bankroll 变动累计成员余额。"""

    return sum(
        (
            calculate_signed_amount(entry_type, amount, adjustment_direction)
            for entry_type, amount, adjustment_direction in entries
        ),
        _ZERO,
    )


def validate_create_policy(
    *,
    member_is_active: bool,
    entry_type: str,
    amount: Decimal,
    adjustment_direction: Optional[str],
    remark: Optional[str],
    current_balance: Decimal,
    has_active_initial: bool,
) -> None:
    """校验新增 bankroll 变动的业务约束。"""

    if entry_type not in _VALID_TYPES:
        raise ValueError("bankroll 变动类型无效。")
    if amount <= _ZERO:
        raise ValueError("bankroll 金额必须大于 0。")
    if entry_type == "adjustment":
        if adjustment_direction not in _VALID_DIRECTIONS:
            raise ValueError("调整记录必须选择增加或减少。")
        if not _has_text(remark):
            raise ValueError("调整记录必须填写原因。")
    elif adjustment_direction is not None:
        raise ValueError("只有调整记录可以填写调整方向。")

    if entry_type == "initial" and has_active_initial:
        raise ValueError("该成员已经存在有效初始 bankroll 记录。")
    if entry_type in _INCREASE_TYPES and not member_is_active:
        raise ValueError("停用成员不能初始化或补充 bankroll。")
    if entry_type == "return" and amount > current_balance:
        raise ValueError("退回金额不能超过成员当前 bankroll 余额。")


def validate_void_policy(*, is_voided: bool, reason: Optional[str]) -> None:
    """校验 bankroll 变动作废规则。"""

    if is_voided:
        raise ValueError("该 bankroll 变动记录已经作废。")
    if not _has_text(reason):
        raise ValueError("作废原因不能为空。")


def _signed_amount_case():
    """构造 SQL 聚合用的余额影响表达式。"""

    return case(
        (BankrollEntry.entry_type.in_(tuple(_INCREASE_TYPES)), BankrollEntry.amount),
        (BankrollEntry.entry_type == "return", -BankrollEntry.amount),
        (
            and_(
                BankrollEntry.entry_type == "adjustment",
                BankrollEntry.adjustment_direction == "increase",
            ),
            BankrollEntry.amount,
        ),
        else_=-BankrollEntry.amount,
    )


def _to_response(entry: BankrollEntry) -> BankrollEntryResponse:
    return BankrollEntryResponse(
        id=entry.id,
        business_date=entry.business_date,
        member_id=entry.member_id,
        member_name=entry.member.name,
        entry_type=entry.entry_type,
        amount=entry.amount,
        adjustment_direction=entry.adjustment_direction,
        signed_amount=calculate_signed_amount(
            entry.entry_type,
            entry.amount,
            entry.adjustment_direction,
        ),
        remark=entry.remark,
        voided_at=entry.voided_at,
        void_reason=entry.void_reason,
        voided_by_member_id=entry.voided_by_member_id,
        voided_by_name=entry.voided_by.name if entry.voided_by else None,
        created_at=entry.created_at,
    )


def _require_admin(operator: Member) -> None:
    if not operator.is_admin:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="无权限：只有管理员才能登记或作废 bankroll 变动",
        )


async def _load_entry(session: AsyncSession, entry_id: uuid.UUID) -> BankrollEntry | None:
    return (
        await session.execute(
            select(BankrollEntry)
            .options(
                selectinload(BankrollEntry.member),
                selectinload(BankrollEntry.voided_by),
            )
            .where(BankrollEntry.id == entry_id)
        )
    ).scalar_one_or_none()


async def _balance(session: AsyncSession, member_id: uuid.UUID) -> Decimal:
    amount = await session.scalar(
        select(func.coalesce(func.sum(_signed_amount_case()), 0)).where(
            BankrollEntry.member_id == member_id,
            BankrollEntry.voided_at.is_(None),
        )
    )
    return Decimal(str(amount or 0))


async def _has_active_initial(session: AsyncSession, member_id: uuid.UUID) -> bool:
    count = await session.scalar(
        select(func.count())
        .select_from(BankrollEntry)
        .where(
            BankrollEntry.member_id == member_id,
            BankrollEntry.entry_type == "initial",
            BankrollEntry.voided_at.is_(None),
        )
    )
    return bool(count)


async def create_entry(
    session: AsyncSession,
    data: BankrollEntryCreate,
    operator: Member,
) -> BankrollEntryResponse:
    """登记成员 bankroll 变动，仅管理员可操作。"""

    _require_admin(operator)
    member = await session.get(Member, data.member_id)
    if member is None:
        raise LookupError(f"成员 {data.member_id} 不存在。")

    current_balance = await _balance(session, data.member_id)
    has_initial = await _has_active_initial(session, data.member_id)
    validate_create_policy(
        member_is_active=member.is_active,
        entry_type=data.entry_type,
        amount=data.amount,
        adjustment_direction=data.adjustment_direction,
        remark=data.remark,
        current_balance=current_balance,
        has_active_initial=has_initial,
    )

    entry = BankrollEntry(
        business_date=data.business_date,
        member_id=data.member_id,
        entry_type=data.entry_type,
        amount=data.amount,
        adjustment_direction=data.adjustment_direction,
        remark=data.remark.strip() if data.remark else None,
    )
    session.add(entry)
    await session.flush()
    loaded = await _load_entry(session, entry.id)
    if loaded is None:
        raise LookupError(f"bankroll 变动记录 {entry.id} 不存在。")
    return _to_response(loaded)


async def void_entry(
    session: AsyncSession,
    entry_id: uuid.UUID,
    data: BankrollEntryVoidCreate,
    operator: Member,
) -> BankrollEntryResponse:
    """作废错误登记的 bankroll 变动，原记录保留但不计入余额。"""

    _require_admin(operator)
    entry = await _load_entry(session, entry_id)
    if entry is None:
        raise LookupError(f"bankroll 变动记录 {entry_id} 不存在。")
    validate_void_policy(is_voided=entry.voided_at is not None, reason=data.reason)
    entry.voided_at = datetime.now(timezone.utc)
    entry.void_reason = data.reason.strip()
    entry.voided_by_member_id = operator.id
    await session.flush()
    loaded = await _load_entry(session, entry.id)
    if loaded is None:
        raise LookupError(f"bankroll 变动记录 {entry.id} 不存在。")
    return _to_response(loaded)


async def list_summary(
    session: AsyncSession,
    operator: Member,
) -> BankrollSummaryResponse:
    """返回当前成员可见范围内的 bankroll 余额。"""

    member_stmt = select(Member).order_by(Member.name)
    if not operator.is_admin:
        member_stmt = member_stmt.where(Member.id == operator.id)
    members = (await session.execute(member_stmt)).scalars().all()
    member_ids = [member.id for member in members]
    balances: dict[uuid.UUID, Decimal] = {}
    if member_ids:
        rows = (
            await session.execute(
                select(BankrollEntry.member_id, func.coalesce(func.sum(_signed_amount_case()), 0))
                .where(
                    BankrollEntry.member_id.in_(member_ids),
                    BankrollEntry.voided_at.is_(None),
                )
                .group_by(BankrollEntry.member_id)
            )
        ).all()
        balances = {member_id: Decimal(str(balance or 0)) for member_id, balance in rows}

    items = [
        BankrollMemberBalance(
            member_id=member.id,
            member_name=member.name,
            role=member.role,
            is_active=member.is_active,
            balance=balances.get(member.id, _ZERO),
        )
        for member in members
    ]
    return BankrollSummaryResponse(
        items=items,
        total_balance=sum((item.balance for item in items), _ZERO),
    )


async def list_entries(
    session: AsyncSession,
    operator: Member,
    member_id: Optional[uuid.UUID] = None,
    entry_type: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    include_voided: bool = False,
    page: int = 1,
    limit: int = 20,
) -> BankrollEntryListResponse:
    """分页返回当前成员可见范围内的 bankroll 变动明细。"""

    if entry_type is not None and entry_type not in _VALID_TYPES:
        raise ValueError("bankroll 变动类型无效。")
    filters = []
    if operator.is_admin:
        if member_id:
            filters.append(BankrollEntry.member_id == member_id)
    else:
        if member_id and member_id != operator.id:
            raise HTTPException(
                status_code=http_status.HTTP_403_FORBIDDEN,
                detail="无权限：只能查看自己的 bankroll 明细",
            )
        filters.append(BankrollEntry.member_id == operator.id)
    if entry_type:
        filters.append(BankrollEntry.entry_type == entry_type)
    if start_date:
        filters.append(BankrollEntry.business_date >= start_date)
    if end_date:
        filters.append(BankrollEntry.business_date <= end_date)
    if not include_voided:
        filters.append(BankrollEntry.voided_at.is_(None))

    where = and_(*filters) if filters else True
    limit = min(limit, 100)
    total = await session.scalar(select(func.count()).select_from(BankrollEntry).where(where)) or 0
    rows = (
        await session.execute(
            select(BankrollEntry)
            .options(
                selectinload(BankrollEntry.member),
                selectinload(BankrollEntry.voided_by),
            )
            .where(where)
            .order_by(desc(BankrollEntry.business_date), desc(BankrollEntry.created_at))
            .offset((page - 1) * limit)
            .limit(limit)
        )
    ).scalars().all()
    return BankrollEntryListResponse(
        items=[_to_response(row) for row in rows],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, -(-total // limit)),
    )
