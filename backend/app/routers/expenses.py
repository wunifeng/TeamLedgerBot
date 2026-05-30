"""成员垫付支出路由（含鉴权、编辑、历史）。"""
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.member import Member
from app.schemas.expense import (
    ExpenseChangeLogResponse,
    MemberExpenseListResponse,
    MemberExpenseResponse,
    MemberExpenseStatusUpdate,
    MemberExpenseUpdate,
)
from app.services import expense_service, telegram_service
from app.services.auth_service import get_current_member

router = APIRouter()
_MAX_RECEIPT_BYTES = 10 * 1024 * 1024
_ALLOWED_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".pdf"}


async def _store_receipt(receipt: Optional[UploadFile]) -> Optional[str]:
    if receipt is None or not receipt.filename:
        return None
    suffix = Path(receipt.filename).suffix.lower()
    if suffix not in _ALLOWED_SUFFIXES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="凭证仅支持 JPG、PNG、WEBP 或 PDF。")
    content = await receipt.read()
    if len(content) > _MAX_RECEIPT_BYTES:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="凭证大小不能超过 10 MB。")
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{suffix}"
    (upload_dir / filename).write_bytes(content)
    return f"/uploads/{filename}"


@router.post(
    "/expenses",
    response_model=MemberExpenseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create member expense",
)
async def create_expense(
    business_date: date = Form(...),
    member_id: uuid.UUID = Form(...),
    amount: Decimal = Form(..., gt=0),
    category_id: Optional[uuid.UUID] = Form(None),
    remark: Optional[str] = Form(None, max_length=500),
    receipt: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> MemberExpenseResponse:
    try:
        result = await expense_service.create_expense(
            db, business_date, member_id, amount, category_id, remark, None, operator=current_member
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    receipt_url = await _store_receipt(receipt)
    if receipt_url:
        result = await expense_service.attach_receipt(db, result.id, receipt_url)
    await telegram_service.notify_member_expense(result, operator_name=current_member.name)
    return result


@router.get("/expenses", response_model=MemberExpenseListResponse, summary="List member expenses")
async def list_expenses(
    member_id: Optional[uuid.UUID] = Query(None),
    reimbursed: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_member),
) -> MemberExpenseListResponse:
    return await expense_service.list_expenses(db, member_id, reimbursed)


@router.patch(
    "/expenses/{expense_id}",
    response_model=MemberExpenseResponse,
    summary="Update member expense",
    description="修改支出的金额、分类或备注。管理员可修改所有人，成员只能修改自己的。",
)
async def update_expense(
    expense_id: uuid.UUID,
    data: MemberExpenseUpdate,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> MemberExpenseResponse:
    try:
        result = await expense_service.update_expense(db, expense_id, data, operator=current_member)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    # 取最新变更日志的 before_data
    from sqlalchemy import select, desc
    from app.models.member_expense import ExpenseChangeLog
    last_log = (await db.execute(
        select(ExpenseChangeLog)
        .where(ExpenseChangeLog.expense_id == expense_id, ExpenseChangeLog.change_type == "update")
        .order_by(desc(ExpenseChangeLog.changed_at))
        .limit(1)
    )).scalar_one_or_none()
    before_data = last_log.before_data if last_log else {}
    await telegram_service.notify_expense_updated(result, operator_name=current_member.name, before_data=before_data)
    return result


@router.get(
    "/expenses/{expense_id}/history",
    response_model=List[ExpenseChangeLogResponse],
    summary="Get expense change history",
)
async def get_expense_history(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_member),
) -> List[ExpenseChangeLogResponse]:
    return await expense_service.get_expense_history(db, expense_id)


@router.patch(
    "/expenses/{expense_id}/reimbursed",
    response_model=MemberExpenseResponse,
    summary="Update reimbursement status",
)
async def update_reimbursed(
    expense_id: uuid.UUID,
    data: MemberExpenseStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: Member = Depends(get_current_member),
) -> MemberExpenseResponse:
    try:
        return await expense_service.update_reimbursed(db, expense_id, data.reimbursed)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/expenses/{expense_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete member expense",
)
async def delete_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_member: Member = Depends(get_current_member),
) -> None:
    try:
        snapshot = await expense_service.delete_expense(db, expense_id, operator=current_member)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    await telegram_service.notify_expense_deleted(snapshot, operator_name=current_member.name)
