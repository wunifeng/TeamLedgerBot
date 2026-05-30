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
    is_admin: Optional[bool] = None


class MemberSetPin(BaseModel):
    """设置或重置成员 PIN。"""
    member_id: uuid.UUID
    pin: str = Field(..., min_length=4, max_length=8, description="4~8 位数字 PIN")


class MemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    role: Optional[str]
    is_active: bool
    is_admin: bool
    created_at: datetime
