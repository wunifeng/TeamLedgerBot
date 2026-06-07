"""成员 bankroll 路由。"""
import logging
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.member import Member
from app.schemas.bankroll import (
    BankrollEntryCreate,
    BankrollEntryListResponse,
    BankrollEntryResponse,
    BankrollEntryVoidCreate,
    BankrollSummaryResponse,
)
from app.services import bankroll_service, telegram_service
from app.services.auth_service import get_current_member

router = APIRouter()
logger = logging.getLogger(__name__)


async def _commit_bankroll_and_notify(
    db: AsyncSession,
    entry: BankrollEntryResponse,
    operator: Member,
    *,
    voided: bool = False,
) -> None:
    """先提交 bankroll 变动，再发送 Telegram，避免通知早于落库。"""

    await db.commit()
    logger.info(
        "Bankroll entry committed before Telegram notification: entry_id=%s member_id=%s operator_id=%s voided=%s",
        entry.id,
        entry.member_id,
        operator.id,
        voided,
    )
    try:
        if voided:
            await telegram_service.notify_bankroll_entry_voided(entry, operator_name=operator.name)
        else:
            await telegram_service.notify_bankroll_entry(entry, operator_name=operator.name)
    except Exception as exc:
        logger.error(
            "Telegram bankroll notification failed after commit: entry_id=%s operator_id=%s error=%s",
            entry.id,
            operator.id,
            exc,
        )


@router.get(
    "/bankroll/summary",
    response_model=BankrollSummaryResponse,
    summary="List bankroll balances",
)
async def get_bankroll_summary(
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> BankrollSummaryResponse:
    return await bankroll_service.list_summary(db, current_member)


@router.get(
    "/bankroll/entries",
    response_model=BankrollEntryListResponse,
    summary="List bankroll entries",
)
async def list_bankroll_entries(
    member_id: Optional[uuid.UUID] = Query(None),
    entry_type: Optional[str] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    include_voided: bool = Query(False),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> BankrollEntryListResponse:
    try:
        return await bankroll_service.list_entries(
            db,
            current_member,
            member_id=member_id,
            entry_type=entry_type,
            start_date=start_date,
            end_date=end_date,
            include_voided=include_voided,
            page=page,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))


@router.post(
    "/bankroll/entries",
    response_model=BankrollEntryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create bankroll entry",
)
async def create_bankroll_entry(
    data: BankrollEntryCreate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> BankrollEntryResponse:
    try:
        result = await bankroll_service.create_entry(db, data, operator=current_member)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    await _commit_bankroll_and_notify(db, result, current_member)
    return result


@router.post(
    "/bankroll/entries/{entry_id}/void",
    response_model=BankrollEntryResponse,
    summary="Void bankroll entry",
)
async def void_bankroll_entry(
    entry_id: uuid.UUID,
    data: BankrollEntryVoidCreate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> BankrollEntryResponse:
    try:
        result = await bankroll_service.void_entry(db, entry_id, data, operator=current_member)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    await _commit_bankroll_and_notify(db, result, current_member, voided=True)
    return result
