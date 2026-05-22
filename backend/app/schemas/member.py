"""Pydantic schemas for Member CRUD operations."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class MemberCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["Nicky"])
    role: Optional[str] = Field(None, max_length=50, examples=["Developer"])


class MemberUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = None


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    role: Optional[str]
    is_active: bool
    created_at: datetime
