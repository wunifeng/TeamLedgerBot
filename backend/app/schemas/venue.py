"""场子配置 API schema。"""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VenueCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    rebate_rate: Decimal = Field(..., gt=0, decimal_places=3)


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    rebate_rate: Optional[Decimal] = Field(None, gt=0, decimal_places=3)
    is_active: Optional[bool] = None


class VenueResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    rebate_rate: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime
