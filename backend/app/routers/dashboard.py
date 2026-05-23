"""Dashboard router — GET /api/dashboard/* analytics endpoints."""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dashboard import (
    CategoryBreakdownResponse,
    DailyTrendResponse,
    MonthlyTrendResponse,
    SummaryResponse,
)
from app.services import reporting_service

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get(
    "/dashboard/summary",
    response_model=SummaryResponse,
    summary="Financial summary",
)
async def get_summary(
    start_date: Optional[datetime] = Query(None, description="Start of date range (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End of date range (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
) -> SummaryResponse:
    """Return aggregate totals (income, expense, salary, net profit) and transaction counts.

    Optionally filter by `start_date` and/or `end_date`.
    """
    return await reporting_service.get_summary(db, start_date=start_date, end_date=end_date)


@router.get(
    "/dashboard/trend/daily",
    response_model=DailyTrendResponse,
    summary="Daily income/expense trend",
)
async def get_daily_trend(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    db: AsyncSession = Depends(get_db),
) -> DailyTrendResponse:
    """Return per-day income and expense totals for the last N days."""
    return await reporting_service.get_daily_trend(db, days=days)


@router.get(
    "/dashboard/trend/monthly",
    response_model=MonthlyTrendResponse,
    summary="Monthly income/expense/salary trend",
)
async def get_monthly_trend(
    months: int = Query(12, ge=1, le=36, description="Number of months to look back"),
    db: AsyncSession = Depends(get_db),
) -> MonthlyTrendResponse:
    """Return per-month income, expense, and salary totals for the last N months."""
    return await reporting_service.get_monthly_trend(db, months=months)


@router.get(
    "/dashboard/category-breakdown",
    response_model=CategoryBreakdownResponse,
    summary="Category-level breakdown",
)
async def get_category_breakdown(
    start_date: Optional[datetime] = Query(None, description="Start of date range (ISO 8601)"),
    end_date: Optional[datetime] = Query(None, description="End of date range (ISO 8601)"),
    db: AsyncSession = Depends(get_db),
) -> CategoryBreakdownResponse:
    """Return income and expense totals grouped by category, with percentage share."""
    return await reporting_service.get_category_breakdown(
        db, start_date=start_date, end_date=end_date
    )
