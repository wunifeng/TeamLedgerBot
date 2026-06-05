"""工资账期与实际发放 API schema。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class SalaryPaymentCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    remark: Optional[str] = Field(None, max_length=500)


class SalaryPaymentVoidCreate(BaseModel):
    reason: Optional[str] = Field(None, max_length=500)


class SalaryPaymentItem(BaseModel):
    id: uuid.UUID
    settlement_id: uuid.UUID
    amount: Decimal
    remark: Optional[str]
    paid_at: datetime
    voided_at: Optional[datetime] = None
    void_reason: Optional[str] = None


class SalarySettlementResponse(BaseModel):
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
    payments: List[SalaryPaymentItem] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SalarySettlementListResponse(BaseModel):
    items: List[SalarySettlementResponse]
    total_payable: Decimal = Decimal("0")
    total_paid: Decimal = Decimal("0")
    total_unpaid: Decimal = Decimal("0")


class SalaryPaymentResponse(BaseModel):
    settlement: SalarySettlementResponse
    payment: SalaryPaymentItem
