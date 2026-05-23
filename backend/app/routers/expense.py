"""Expense router — POST /api/expense."""
import logging

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.transaction import ExpenseCreate, TransactionWriteResponse
from app.services import telegram_service, transaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/expense",
    response_model=TransactionWriteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record expense",
)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
) -> TransactionWriteResponse:
    """Record a new expense transaction.

    After saving, sends a Telegram notification and any triggered risk alerts
    (high amount / duplicate / high frequency) synchronously before returning.
    """
    tx, alerts = await transaction_service.create_expense(db, data)

    # ── Telegram: record notification ─────────────────────────
    await telegram_service.notify_expense(
        member_name=tx.member_name,
        amount=tx.amount,
        category_name=tx.category_name,
        remark=tx.remark,
        created_at=tx.created_at,
    )

    # ── Telegram: risk alerts ──────────────────────────────────
    for alert in alerts:
        if alert == "high_amount":
            await telegram_service.alert_high_amount(tx.member_name, tx.amount, "expense", tx.created_at)
        elif alert == "duplicate":
            await telegram_service.alert_duplicate(tx.member_name, tx.amount, "expense", tx.created_at)
        elif alert == "high_frequency":
            await telegram_service.alert_high_frequency(tx.member_name, "expense", tx.created_at)

    return TransactionWriteResponse(transaction=tx, alerts=alerts)
