"""Pydantic schemas for Category CRUD operations."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.enums import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Food"])
    type: CategoryType
    description: Optional[str] = Field(None, max_length=255)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    type: CategoryType
    description: Optional[str]
    is_active: bool
    created_at: datetime
