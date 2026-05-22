"""Risk detection validation rules — run before committing transactions."""
import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.enums import TransactionType
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


async def check_high_amount(amount: Decimal) -> bool:
    """Rule 1: Single amount exceeds risk threshold."""
    return float(amount) > settings.RISK_HIGH_AMOUNT_THRESHOLD


async def check_duplicate(
    session: AsyncSession,
    member_id: uuid.UUID,
    amount: Decimal,
    category_id: Optional[uuid.UUID],
    tx_type: TransactionType,
) -> bool:
    """Rule 2: Same member submits identical amount+category within time window."""
    since = datetime.now(timezone.utc) - timedelta(
        seconds=settings.RISK_DUPLICATE_WINDOW_SECONDS
    )
    stmt = (
        select(func.count())
        .select_from(Transaction)
        .where(
            and_(
                Transaction.member_id == member_id,
                Transaction.amount == amount,
                Transaction.type == tx_type.value,
                Transaction.category_id == category_id,
                Transaction.created_at >= since,
            )
        )
    )
    count = await session.scalar(stmt)
    return (count or 0) > 0


async def check_high_frequency(
    session: AsyncSession,
    member_id: uuid.UUID,
) -> bool:
    """Rule 3: Same member submits too many transactions within time window."""
    since = datetime.now(timezone.utc) - timedelta(
        seconds=settings.RISK_FREQUENCY_WINDOW_SECONDS
    )
    stmt = (
        select(func.count())
        .select_from(Transaction)
        .where(
            and_(
                Transaction.member_id == member_id,
                Transaction.created_at >= since,
            )
        )
    )
    count = await session.scalar(stmt)
    return (count or 0) >= settings.RISK_FREQUENCY_LIMIT


async def run_all_checks(
    session: AsyncSession,
    member_id: uuid.UUID,
    amount: Decimal,
    category_id: Optional[uuid.UUID],
    tx_type: TransactionType,
) -> list[str]:
    """Run all risk checks and return list of triggered alert types."""
    alerts: list[str] = []
    if await check_high_amount(amount):
        alerts.append("high_amount")
    if await check_duplicate(session, member_id, amount, category_id, tx_type):
        alerts.append("duplicate")
    if await check_high_frequency(session, member_id):
        alerts.append("high_frequency")
    return alerts
