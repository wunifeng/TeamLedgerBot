"""Pydantic schemas for Transaction write and read operations."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.enums import TransactionType


# ── Write Schemas ──────────────────────────────────────────────────────────────

class IncomeCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, examples=[1500.00])
    category_id: Optional[uuid.UUID] = None
    member_id: uuid.UUID
    remark: Optional[str] = Field(None, max_length=500)
    # If provided, overrides server time (useful for retroactive entries)
    timestamp: Optional[datetime] = None


class ExpenseCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2, examples=[120.00])
    category_id: Optional[uuid.UUID] = None
    member_id: uuid.UUID
    remark: Optional[str] = Field(None, max_length=500)
    timestamp: Optional[datetime] = None


class SalaryCreate(BaseModel):
    member_id: uuid.UUID
    salary_amount: Decimal = Field(..., gt=0, decimal_places=2)
    bonus: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    remark: Optional[str] = Field(None, max_length=500)
    timestamp: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_bonus(self) -> "SalaryCreate":
        if self.bonus is not None and self.bonus < 0:
            raise ValueError("bonus must be non-negative")
        return self


# ── Read Schemas ───────────────────────────────────────────────────────────────

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    type: TransactionType
    amount: Decimal
    category_id: Optional[uuid.UUID]
    category_name: Optional[str] = None
    member_id: uuid.UUID
    member_name: str = ""
    remark: Optional[str]
    bonus: Optional[Decimal]
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def populate_denormalized(self) -> "TransactionResponse":
        """Populate denormalized fields from ORM relationships if available."""
        # These will be set by the service layer when building the response
        return self


class TransactionListResponse(BaseModel):
    items: List[TransactionResponse]
    total: int
    page: int
    limit: int
    pages: int


class TransactionWriteResponse(BaseModel):
    """Response returned by income / expense / salary write endpoints."""
    transaction: TransactionResponse
    alerts: List[str] = []
