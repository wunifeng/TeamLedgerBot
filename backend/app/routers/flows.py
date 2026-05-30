"""每日业务流水路由（含鉴权、编辑、历史）。"""
import uuid
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.member import Member
from app.schemas.flow import (
    DailyFlowCreate,
    DailyFlowListResponse,
    DailyFlowResponse,
    DailyFlowUpdate,
    FlowChangeLogResponse,
)
from app.services import flow_service, telegram_service
from app.services.auth_service import get_current_member

router = APIRouter()


@router.post(
    "/flows",
    response_model=DailyFlowResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create daily flow",
)
async def create_flow(
    data: DailyFlowCreate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> DailyFlowResponse:
    try:
        result = await flow_service.create_report(db, data, operator=current_member)
    except flow_service.DuplicateFlowError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    await telegram_service.notify_daily_flow(result, operator_name=current_member.name)
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
    _: Member = Depends(get_current_member),
) -> DailyFlowListResponse:
    return await flow_service.list_reports(db, member_id, venue_id, start_date, end_date, page, limit)


@router.patch(
    "/flows/{flow_id}",
    response_model=DailyFlowResponse,
    summary="Update daily flow",
    description="修改流水金额字段（本金/点码/输反/盈亏/备注），工资自动重算。管理员可修改所有人，成员只能修改自己的。",
)
async def update_flow(
    flow_id: uuid.UUID,
    data: DailyFlowUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> DailyFlowResponse:
    try:
        result = await flow_service.update_report(db, flow_id, data, operator=current_member)
    except flow_service.DuplicateFlowError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))

    # 获取旧快照（用于 Telegram 通知）—— 直接从 change_log 取 before_data
    from sqlalchemy import select, desc
    from app.models.daily_flow_report import FlowChangeLog
    last_log = (await db.execute(
        select(FlowChangeLog)
        .where(FlowChangeLog.flow_id == flow_id, FlowChangeLog.change_type == "update")
        .order_by(desc(FlowChangeLog.changed_at))
        .limit(1)
    )).scalar_one_or_none()
    before_data = last_log.before_data if last_log else {}
    await telegram_service.notify_flow_updated(result, operator_name=current_member.name, before_data=before_data)
    return result


@router.get(
    "/flows/{flow_id}/history",
    response_model=List[FlowChangeLogResponse],
    summary="Get flow change history",
)
async def get_flow_history(
    flow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_member),
) -> List[FlowChangeLogResponse]:
    return await flow_service.get_flow_history(db, flow_id)


@router.delete(
    "/flows/{flow_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete daily flow",
)
async def delete_flow(
    flow_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> None:
    try:
        snapshot = await flow_service.delete_report(db, flow_id, operator=current_member)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    await telegram_service.notify_flow_deleted(snapshot, operator_name=current_member.name)
