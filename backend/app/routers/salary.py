"""Salary router — salary transactions and period settlements."""
import logging
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.salary import (
    SalaryPaymentCreate,
    SalaryPaymentResponse,
    SalarySettlementCreate,
    SalarySettlementListResponse,
    SalarySettlementResponse,
)
from app.schemas.transaction import SalaryCreate, TransactionWriteResponse
from app.services import salary_service, telegram_service, transaction_service

logger = logging.getLogger(__name__)
router = APIRouter()


async def _send_salary_notifications(
    tx,
    alerts: list[str],
) -> None:
    await telegram_service.notify_salary(
        member_name=tx.member_name,
        salary_amount=tx.amount,
        bonus=tx.bonus,
        remark=tx.remark,
        created_at=tx.created_at,
    )

    for alert in alerts:
        alert_amount = tx.amount + (tx.bonus or Decimal("0"))
        if alert == "high_amount":
            await telegram_service.alert_high_amount(tx.member_name, alert_amount, "salary", tx.created_at)
        elif alert == "duplicate":
            await telegram_service.alert_duplicate(tx.member_name, alert_amount, "salary", tx.created_at)
        elif alert == "high_frequency":
            await telegram_service.alert_high_frequency(tx.member_name, "salary", tx.created_at)


@router.get(
    "/salary/settlements",
    response_model=SalarySettlementListResponse,
    summary="List salary settlements",
)
async def list_salary_settlements(
    period_start: Optional[date] = Query(None, description="账期开始日期"),
    period_end: Optional[date] = Query(None, description="账期结束日期"),
    include_inactive: bool = Query(True, description="是否包含已停用成员"),
    db: AsyncSession = Depends(get_db),
) -> SalarySettlementListResponse:
    """返回指定账期的成员工资应付、已付和未付汇总。"""
    return await salary_service.list_settlements(
        db,
        period_start=period_start,
        period_end=period_end,
        include_inactive=include_inactive,
    )


@router.post(
    "/salary/settlements",
    response_model=SalarySettlementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create or update a salary settlement",
)
async def upsert_salary_settlement(
    data: SalarySettlementCreate,
    db: AsyncSession = Depends(get_db),
) -> SalarySettlementResponse:
    """设置或更新某个成员在指定账期内的应付工资。"""
    try:
        return await salary_service.create_or_update_settlement(db, data)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/salary/settlements/{settlement_id}/pay",
    response_model=SalaryPaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Pay a salary settlement",
)
async def pay_salary_settlement(
    settlement_id: uuid.UUID,
    data: SalaryPaymentCreate,
    db: AsyncSession = Depends(get_db),
) -> SalaryPaymentResponse:
    """发放账期工资，并同步生成 salary 交易流水。"""
    try:
        result = await salary_service.pay_settlement(db, settlement_id, data)
    except NoResultFound:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Salary settlement {settlement_id} not found.",
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    await _send_salary_notifications(result.transaction, result.alerts)
    return result


@router.post(
    "/salary",
    response_model=TransactionWriteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record salary disbursement",
)
async def create_salary(
    data: SalaryCreate,
    db: AsyncSession = Depends(get_db),
) -> TransactionWriteResponse:
    """Record a salary (and optional bonus) disbursement.

    After saving, sends a Telegram notification and any triggered risk alerts
    (high amount / duplicate / high frequency) synchronously before returning.
    """
    tx, alerts = await transaction_service.create_salary(db, data)

    await _send_salary_notifications(tx, alerts)

    return TransactionWriteResponse(transaction=tx, alerts=alerts)
