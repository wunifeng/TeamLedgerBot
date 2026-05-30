"""业务仪表盘路由。"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.dashboard import DailyTrendResponse, SummaryResponse, VenueBreakdownResponse
from app.services import reporting_service

router = APIRouter()


@router.get("/dashboard/summary", response_model=SummaryResponse, summary="Business summary")
async def get_summary(db: AsyncSession = Depends(get_db)) -> SummaryResponse:
    return await reporting_service.get_summary(db)


@router.get("/dashboard/trend/daily", response_model=DailyTrendResponse, summary="Daily business trend")
async def get_daily_trend(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> DailyTrendResponse:
    return await reporting_service.get_daily_trend(db, days)


@router.get("/dashboard/venue-breakdown", response_model=VenueBreakdownResponse, summary="Venue breakdown")
async def get_venue_breakdown(db: AsyncSession = Depends(get_db)) -> VenueBreakdownResponse:
    return await reporting_service.get_venue_breakdown(db)
