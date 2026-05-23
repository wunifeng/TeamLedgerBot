"""Transactions router — GET /api/transactions (list + detail) and soft-delete."""
import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import TransactionType
from app.schemas.transaction import TransactionListResponse, TransactionResponse
from app.services import transaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/transactions",
    response_model=TransactionListResponse,
    summary="List transactions",
)
async def list_transactions(
    type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    member_id: Optional[uuid.UUID] = Query(None, description="Filter by member UUID"),
    start_date: Optional[datetime] = Query(None, description="Earliest created_at (inclusive), ISO 8601"),
    end_date: Optional[datetime] = Query(None, description="Latest created_at (inclusive), ISO 8601"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Records per page"),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    """Return paginated, filtered list of non-deleted transactions, newest first."""
    return await transaction_service.list_transactions(
        session=db,
        tx_type=type.value if type else None,
        member_id=member_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
    summary="Get a transaction by ID",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    """Retrieve a single non-deleted transaction by UUID."""
    try:
        return await transaction_service.get_transaction(db, transaction_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found.",
        )


@router.delete(
    "/transactions/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a transaction",
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Mark a transaction as deleted (is_deleted=True). Records are never physically removed."""
    try:
        await transaction_service.delete_transaction(db, transaction_id)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction {transaction_id} not found or already deleted.",
        )
