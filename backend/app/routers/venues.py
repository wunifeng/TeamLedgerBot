"""场子配置路由。"""
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.venue import Venue
from app.schemas.venue import VenueCreate, VenueResponse, VenueUpdate
from app.services.salary_rule_service import list_games, list_rebate_rates, supports_rebate_rate

router = APIRouter()


async def _get_venue_or_404(session: AsyncSession, venue_id: uuid.UUID) -> Venue:
    venue = await session.get(Venue, venue_id)
    if venue is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"场子 {venue_id} 不存在。")
    return venue


@router.get("/venues/games", response_model=List[str], summary="List fixed games")
async def get_games() -> List[str]:
    return list_games()


@router.get("/venues/rebate-rates", response_model=List[float], summary="List supported rebate rates")
async def get_rebate_rates() -> List[float]:
    return [float(rate) for rate in list_rebate_rates()]


@router.get("/venues", response_model=List[VenueResponse], summary="List venues")
async def list_venues(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> List[VenueResponse]:
    stmt = select(Venue).order_by(Venue.name)
    if not include_inactive:
        stmt = stmt.where(Venue.is_active.is_(True))
    return (await db.execute(stmt)).scalars().all()  # type: ignore[return-value]


@router.post("/venues", response_model=VenueResponse, status_code=status.HTTP_201_CREATED, summary="Create venue")
async def create_venue(data: VenueCreate, db: AsyncSession = Depends(get_db)) -> VenueResponse:
    if not supports_rebate_rate(data.rebate_rate):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="场子输返比例没有对应工资配置。")
    venue = Venue(**data.model_dump())
    db.add(venue)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"场子 {data.name} 已存在。") from exc
    await db.refresh(venue)
    return venue  # type: ignore[return-value]


@router.patch("/venues/{venue_id}", response_model=VenueResponse, summary="Update venue")
async def update_venue(
    venue_id: uuid.UUID,
    data: VenueUpdate,
    db: AsyncSession = Depends(get_db),
) -> VenueResponse:
    venue = await _get_venue_or_404(db, venue_id)
    update_data = data.model_dump(exclude_unset=True)
    rebate_rate = update_data.get("rebate_rate")
    if rebate_rate is not None and not supports_rebate_rate(rebate_rate):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="场子输返比例没有对应工资配置。")
    for field, value in update_data.items():
        setattr(venue, field, value)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="场子名称已存在。") from exc
    await db.refresh(venue)
    return venue  # type: ignore[return-value]
