"""每日业务流水路由。"""
import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.flow import DailyFlowCreate, DailyFlowListResponse, DailyFlowResponse
from app.services import flow_service, telegram_service

router = APIRouter()


@router.post("/flows", response_model=DailyFlowResponse, status_code=status.HTTP_201_CREATED, summary="Create daily flow")
async def create_flow(data: DailyFlowCreate, db: AsyncSession = Depends(get_db)) -> DailyFlowResponse:
    try:
        result = await flow_service.create_report(db, data)
    except flow_service.DuplicateFlowError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    await telegram_service.notify_daily_flow(result)
    return result


@router.get("/flows", response_model=DailyFlowListResponse, summary="List daily flows")
async def list_flows(
    member_id: Optional[uuid.UUID] = Query(None),
    venue_id: Optional[uuid.UUID] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DailyFlowListResponse:
    return await flow_service.list_reports(db, member_id, venue_id, start_date, end_date, page, limit)


@router.delete("/flows/{flow_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete daily flow")
async def delete_flow(flow_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await flow_service.delete_report(db, flow_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
