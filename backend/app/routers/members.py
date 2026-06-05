"""Members router — full CRUD /api/members."""
import uuid
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberResponse, MemberUpdate
from app.services.auth_service import get_current_member

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_member_or_404(session: AsyncSession, member_id: uuid.UUID) -> Member:
    """Fetch a Member by ID or raise 404."""
    result = await session.execute(
        select(Member).where(Member.id == member_id)
    )
    member = result.scalar_one_or_none()
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Member {member_id} not found.",
        )
    return member


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/members",
    response_model=List[MemberResponse],
    summary="List members",
)
async def list_members(
    include_inactive: bool = Query(False, description="If true, include inactive members"),
    db: AsyncSession = Depends(get_db),
) -> List[MemberResponse]:
    """Return all members. By default only active members are returned."""
    stmt = select(Member).order_by(Member.name)
    if not include_inactive:
        stmt = stmt.where(Member.is_active.is_(True))
    result = await db.execute(stmt)
    return result.scalars().all()  # type: ignore[return-value]


@router.post(
    "/members",
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a member",
)
async def create_member(
    data: MemberCreate,
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Create a new team member. Member name must be unique."""
    member = Member(name=data.name, role=data.role)
    db.add(member)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A member with name '{data.name}' already exists.",
        )
    await db.refresh(member)
    return member  # type: ignore[return-value]


@router.get(
    "/members/{member_id}",
    response_model=MemberResponse,
    summary="Get a member by ID",
)
async def get_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Retrieve a single member by UUID."""
    member = await _get_member_or_404(db, member_id)
    return member  # type: ignore[return-value]


@router.patch(
    "/members/{member_id}",
    response_model=MemberResponse,
    summary="Partially update a member",
)
async def update_member(
    member_id: uuid.UUID,
    data: MemberUpdate,
    db: AsyncSession = Depends(get_db),
) -> MemberResponse:
    """Update one or more fields of a member (partial update)."""
    member = await _get_member_or_404(db, member_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(member, field, value)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A member with name '{data.name}' already exists.",
        )
    await db.refresh(member)
    return member  # type: ignore[return-value]


@router.delete(
    "/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a member",
)
async def delete_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> None:
    """停用成员账号，保留历史业务数据。"""
    if not current_member.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限：只有管理员才能停用成员",
        )
    if current_member.id == member_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限：不能停用当前登录成员",
        )
    member = await _get_member_or_404(db, member_id)
    if not member.is_active:
        return
    member.is_active = False
    await db.flush()
