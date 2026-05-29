"""薪资账期结算 API schema。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.transaction import TransactionResponse


class SalarySettlementCreate(BaseModel):
    member_id: uuid.UUID
    period_start: date
    period_end: date
    payable_amount: Decimal = Field(..., gt=0, decimal_places=2)
    remark: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_period(self) -> "SalarySettlementCreate":
        if self.period_end < self.period_start:
            raise ValueError("period_end must be greater than or equal to period_start")
        return self


class SalaryPaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    bonus: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    remark: Optional[str] = Field(None, max_length=500)
    timestamp: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_bonus(self) -> "SalaryPaymentCreate":
        if self.bonus is not None and self.bonus < 0:
            raise ValueError("bonus must be non-negative")
        return self


class SalarySettlementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    member_id: uuid.UUID
    member_name: str
    period_start: date
    period_end: date
    payable_amount: Decimal
    paid_amount: Decimal
    unpaid_amount: Decimal
    status: str
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime


class SalarySettlementListResponse(BaseModel):
    items: List[SalarySettlementResponse]
    total_payable: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    total_unpaid: Decimal = Decimal("0")


class SalaryPaymentResponse(BaseModel):
    settlement: SalarySettlementResponse
    transaction: TransactionResponse
    alerts: List[str] = []
