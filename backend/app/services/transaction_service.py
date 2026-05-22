"""Transaction service — create income/expense/salary, run risk checks."""
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.enums import TransactionType
from app.models.transaction import Transaction
from app.schemas.transaction import (
    ExpenseCreate, IncomeCreate, SalaryCreate,
    TransactionListResponse, TransactionResponse,
)
from app.services import validation_service

logger = logging.getLogger(__name__)


# ── Helper ─────────────────────────────────────────────────────────────────────

def _to_response(tx: Transaction) -> TransactionResponse:
    return TransactionResponse(
        id=tx.id,
        type=tx.type,
        amount=tx.amount,
        category_id=tx.category_id,
        category_name=tx.category.name if tx.category else None,
        member_id=tx.member_id,
        member_name=tx.member.name if tx.member else "",
        remark=tx.remark,
        bonus=tx.bonus,
        created_at=tx.created_at,
        updated_at=tx.updated_at,
    )


async def _load_tx(session: AsyncSession, tx_id: uuid.UUID) -> Transaction:
    """Reload transaction with relationships."""
    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.member), selectinload(Transaction.category))
        .where(Transaction.id == tx_id)
    )
    result = await session.execute(stmt)
    return result.scalar_one()


# ── Create operations ──────────────────────────────────────────────────────────

async def create_income(
    session: AsyncSession, data: IncomeCreate
) -> tuple[TransactionResponse, list[str]]:
    alerts = await validation_service.run_all_checks(
        session, data.member_id, data.amount, data.category_id, TransactionType.income
    )
    tx = Transaction(
        type=TransactionType.income.value,
        amount=data.amount,
        category_id=data.category_id,
        member_id=data.member_id,
        remark=data.remark,
        **({"created_at": data.timestamp} if data.timestamp else {}),
    )
    session.add(tx)
    await session.flush()
    tx = await _load_tx(session, tx.id)
    return _to_response(tx), alerts


async def create_expense(
    session: AsyncSession, data: ExpenseCreate
) -> tuple[TransactionResponse, list[str]]:
    alerts = await validation_service.run_all_checks(
        session, data.member_id, data.amount, data.category_id, TransactionType.expense
    )
    tx = Transaction(
        type=TransactionType.expense.value,
        amount=data.amount,
        category_id=data.category_id,
        member_id=data.member_id,
        remark=data.remark,
        **({"created_at": data.timestamp} if data.timestamp else {}),
    )
    session.add(tx)
    await session.flush()
    tx = await _load_tx(session, tx.id)
    return _to_response(tx), alerts


async def create_salary(
    session: AsyncSession, data: SalaryCreate
) -> tuple[TransactionResponse, list[str]]:
    alerts = await validation_service.run_all_checks(
        session, data.member_id, data.salary_amount, None, TransactionType.salary
    )
    tx = Transaction(
        type=TransactionType.salary.value,
        amount=data.salary_amount,
        category_id=None,
        member_id=data.member_id,
        bonus=data.bonus,
        remark=data.remark,
        **({"created_at": data.timestamp} if data.timestamp else {}),
    )
    session.add(tx)
    await session.flush()
    tx = await _load_tx(session, tx.id)
    return _to_response(tx), alerts


# ── List / query ───────────────────────────────────────────────────────────────

async def list_transactions(
    session: AsyncSession,
    tx_type: Optional[str] = None,
    member_id: Optional[uuid.UUID] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 20,
) -> TransactionListResponse:
    limit = min(limit, 100)
    offset = (page - 1) * limit

    filters = []
    if tx_type:
        filters.append(Transaction.type == tx_type)
    if member_id:
        filters.append(Transaction.member_id == member_id)
    if start_date:
        filters.append(Transaction.created_at >= start_date)
    if end_date:
        filters.append(Transaction.created_at <= end_date)

    where = and_(*filters) if filters else True

    count_stmt = select(func.count()).select_from(Transaction).where(where)
    total = await session.scalar(count_stmt) or 0

    stmt = (
        select(Transaction)
        .options(selectinload(Transaction.member), selectinload(Transaction.category))
        .where(where)
        .order_by(desc(Transaction.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await session.execute(stmt)
    rows = result.scalars().all()

    return TransactionListResponse(
        items=[_to_response(r) for r in rows],
        total=total,
        page=page,
        limit=limit,
        pages=max(1, -(-total // limit)),  # ceiling division
    )
