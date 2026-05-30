"""成员垫付支出 API schema。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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


class MemberExpenseUpdate(BaseModel):
    """可编辑的支出字段（金额/分类/备注），均为可选。"""
    amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    category_id: Optional[uuid.UUID] = None
    remark: Optional[str] = Field(None, max_length=500)


class MemberExpenseListResponse(BaseModel):
    items: List[MemberExpenseResponse]
    total_amount: Decimal
    total_unreimbursed: Decimal


class MemberExpenseStatusUpdate(BaseModel):
    reimbursed: bool


class ExpenseChangeLogResponse(BaseModel):
    """支出变更历史单条记录。"""
    id: uuid.UUID
    expense_id: uuid.UUID
    changed_at: datetime
    operator_name: str
    change_type: str  # create | update | delete
    before_data: Optional[Dict[str, Any]]
    after_data: Optional[Dict[str, Any]]
