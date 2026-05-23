"""Categories router — full CRUD /api/categories."""
import uuid
import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.enums import CategoryType
from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_category_or_404(session: AsyncSession, category_id: uuid.UUID) -> Category:
    """Fetch a Category by ID or raise 404."""
    result = await session.execute(
        select(Category).where(Category.id == category_id)
    )
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category {category_id} not found.",
        )
    return category


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.get(
    "/categories",
    response_model=List[CategoryResponse],
    summary="List categories",
)
async def list_categories(
    type: Optional[CategoryType] = Query(None, description="Filter by type: income or expense"),
    include_inactive: bool = Query(False, description="If true, include inactive categories"),
    db: AsyncSession = Depends(get_db),
) -> List[CategoryResponse]:
    """Return categories, optionally filtered by type. Active categories only by default."""
    stmt = select(Category).order_by(Category.type, Category.name)
    if type is not None:
        stmt = stmt.where(Category.type == type.value)
    if not include_inactive:
        stmt = stmt.where(Category.is_active.is_(True))
    result = await db.execute(stmt)
    return result.scalars().all()  # type: ignore[return-value]


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a category",
)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """Create a new income or expense category. Name+type combination must be unique."""
    category = Category(
        name=data.name,
        type=data.type.value,
        description=data.description,
    )
    db.add(category)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category with name '{data.name}' and type '{data.type}' already exists.",
        )
    await db.refresh(category)
    return category  # type: ignore[return-value]


@router.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Get a category by ID",
)
async def get_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """Retrieve a single category by UUID."""
    category = await _get_category_or_404(db, category_id)
    return category  # type: ignore[return-value]


@router.patch(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    summary="Partially update a category",
)
async def update_category(
    category_id: uuid.UUID,
    data: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
) -> CategoryResponse:
    """Update one or more fields of a category (partial update)."""
    category = await _get_category_or_404(db, category_id)
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A category with name '{data.name}' of this type already exists.",
        )
    await db.refresh(category)
    return category  # type: ignore[return-value]


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Soft-delete a category",
)
async def delete_category(
    category_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Deactivate (soft-delete) a category by setting is_active=False."""
    category = await _get_category_or_404(db, category_id)
    category.is_active = False
    await db.flush()
