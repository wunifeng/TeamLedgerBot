"""成员垫付支出 API schema。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel


class MemberExpenseResponse(BaseModel):
    id: uuid.UUID
    business_date: date
    member_id: uuid.UUID
    member_name: str
    category_id: Optional[uuid.UUID]
    category_name: Optional[str]
    amount: Decimal
    remark: Optional[str]
    receipt_url: Optional[str]
    reimbursed: bool
    created_at: datetime
    updated_at: datetime


class MemberExpenseListResponse(BaseModel):
    items: List[MemberExpenseResponse]
    total_amount: Decimal
    total_unreimbursed: Decimal


class MemberExpenseStatusUpdate(BaseModel):
    reimbursed: bool
