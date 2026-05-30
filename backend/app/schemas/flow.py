"""每日业务流水 API schema。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DailyFlowCreate(BaseModel):
    business_date: date
    member_id: uuid.UUID
    venue_id: uuid.UUID
    game: str = Field(..., min_length=1, max_length=50)
    card_number: str = Field(default="0", min_length=1, max_length=100)
    principal: Decimal = Field(..., ge=0, decimal_places=2)
    chip_code: Decimal = Field(..., ge=0, decimal_places=2)
    loss_rebate: Decimal = Field(..., ge=0, decimal_places=2)
    profit_loss: Decimal = Field(..., decimal_places=2)
    remark: Optional[str] = Field(None, max_length=500)


class DailyFlowUpdate(BaseModel):
    """可编辑的流水字段（本金/点码/输反/盈亏/备注），均为可选以支持部分更新。"""
    principal: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    chip_code: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    loss_rebate: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    profit_loss: Optional[Decimal] = Field(None, decimal_places=2)
    remark: Optional[str] = Field(None, max_length=500)


class DailyFlowResponse(BaseModel):
    id: uuid.UUID
    business_date: date
    member_id: uuid.UUID
    member_name: str
    venue_id: uuid.UUID
    venue_name: str
    rebate_rate: Decimal
    game: str
    card_number: str
    principal: Decimal
    chip_code: Decimal
    loss_rebate: Decimal
    profit_loss: Decimal
    salary_amount: Decimal
    salary_rule_description: str
    remark: Optional[str]
    created_at: datetime
    updated_at: datetime


class FlowChangeLogResponse(BaseModel):
    """流水变更历史单条记录。"""
    id: uuid.UUID
    flow_id: uuid.UUID
    changed_at: datetime
    operator_name: str
    change_type: str  # create | update | delete
    before_data: Optional[Dict[str, Any]]
    after_data: Optional[Dict[str, Any]]


class DailyFlowListResponse(BaseModel):
    items: List[DailyFlowResponse]
    total: int
    page: int
    limit: int
    pages: int
