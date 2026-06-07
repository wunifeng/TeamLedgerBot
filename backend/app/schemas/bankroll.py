"""成员 bankroll API schema。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, model_validator

BankrollEntryType = Literal["initial", "top_up", "return", "adjustment"]
BankrollAdjustmentDirection = Literal["increase", "decrease"]


def _has_text(value: Optional[str]) -> bool:
    return bool(value and value.strip())


class BankrollEntryCreate(BaseModel):
    business_date: date
    member_id: uuid.UUID
    entry_type: BankrollEntryType
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    adjustment_direction: Optional[BankrollAdjustmentDirection] = None
    remark: Optional[str] = Field(None, max_length=500)

    @model_validator(mode="after")
    def validate_adjustment_fields(self) -> "BankrollEntryCreate":
        if self.entry_type == "adjustment":
            if self.adjustment_direction is None:
                raise ValueError("调整记录必须选择增加或减少。")
            if not _has_text(self.remark):
                raise ValueError("调整记录必须填写原因。")
            return self
        if self.adjustment_direction is not None:
            raise ValueError("只有调整记录可以填写调整方向。")
        return self


class BankrollEntryVoidCreate(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)

    @model_validator(mode="after")
    def validate_reason(self) -> "BankrollEntryVoidCreate":
        if not self.reason.strip():
            raise ValueError("作废原因不能为空。")
        return self


class BankrollEntryResponse(BaseModel):
    id: uuid.UUID
    business_date: date
    member_id: uuid.UUID
    member_name: str
    entry_type: str
    amount: Decimal
    adjustment_direction: Optional[str]
    signed_amount: Decimal
    remark: Optional[str]
    voided_at: Optional[datetime]
    void_reason: Optional[str]
    voided_by_member_id: Optional[uuid.UUID]
    voided_by_name: Optional[str]
    created_at: datetime


class BankrollEntryListResponse(BaseModel):
    items: List[BankrollEntryResponse]
    total: int
    page: int
    limit: int
    pages: int


class BankrollMemberBalance(BaseModel):
    member_id: uuid.UUID
    member_name: str
    role: Optional[str]
    is_active: bool
    balance: Decimal = Decimal("0")


class BankrollSummaryResponse(BaseModel):
    items: List[BankrollMemberBalance]
    total_balance: Decimal = Decimal("0")
