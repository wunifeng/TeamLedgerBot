"""工资月结与发放路由。"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.member import Member
from app.schemas.salary import (
    SalaryPaymentCreate,
    SalaryPaymentResponse,
    SalaryPaymentVoidCreate,
    SalarySettlementListResponse,
)
from app.services import salary_service, telegram_service
from app.services.auth_service import get_current_member

router = APIRouter()


def _require_admin(member: Member) -> None:
    """工资实发会影响账务状态，仅管理员可登记或作废。"""
    if not member.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限：只有管理员才能登记或作废工资发放",
        )


@router.get("/salary/settlements", response_model=SalarySettlementListResponse, summary="List salary settlements")
async def list_salary_settlements(
    period_start: date = Query(..., description="月度账期开始日期"),
    period_end: date = Query(..., description="月度账期结束日期"),
    include_inactive: bool = Query(True),
    db: AsyncSession = Depends(get_db),
) -> SalarySettlementListResponse:
    if period_start.day != 1 or period_start.month != period_end.month or period_start.year != period_end.year:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="工资账期必须为同一个自然月。")
    return await salary_service.list_settlements(db, period_start, period_end, include_inactive)


@router.post("/salary/settlements/{settlement_id}/pay", response_model=SalaryPaymentResponse, status_code=status.HTTP_201_CREATED, summary="Pay salary settlement")
async def pay_salary_settlement(
    settlement_id: uuid.UUID,
    data: SalaryPaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> SalaryPaymentResponse:
    _require_admin(current_member)
    try:
        result = await salary_service.pay_settlement(db, settlement_id, data)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    await telegram_service.notify_salary_payment(result)
    return result


@router.post("/salary/payments/{payment_id}/void", response_model=SalaryPaymentResponse, summary="Void salary payment")
async def void_salary_payment(
    payment_id: uuid.UUID,
    data: SalaryPaymentVoidCreate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> SalaryPaymentResponse:
    _require_admin(current_member)
    try:
        result = await salary_service.void_payment(db, payment_id, data, current_member.id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    await telegram_service.notify_salary_payment_voided(result, current_member.name)
    return result
