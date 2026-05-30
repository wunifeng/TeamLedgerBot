"""成员垫付支出路由。"""
import uuid
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas.expense import MemberExpenseListResponse, MemberExpenseResponse, MemberExpenseStatusUpdate
from app.services import expense_service, telegram_service

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


@router.post("/expenses", response_model=MemberExpenseResponse, status_code=status.HTTP_201_CREATED, summary="Create member expense")
async def create_expense(
    business_date: date = Form(...),
    member_id: uuid.UUID = Form(...),
    amount: Decimal = Form(..., gt=0),
    category_id: Optional[uuid.UUID] = Form(None),
    remark: Optional[str] = Form(None, max_length=500),
    receipt: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db),
) -> MemberExpenseResponse:
    try:
        result = await expense_service.create_expense(db, business_date, member_id, amount, category_id, remark, None)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    receipt_url = await _store_receipt(receipt)
    if receipt_url:
        result = await expense_service.attach_receipt(db, result.id, receipt_url)
    await telegram_service.notify_member_expense(result)
    return result


@router.get("/expenses", response_model=MemberExpenseListResponse, summary="List member expenses")
async def list_expenses(
    member_id: Optional[uuid.UUID] = Query(None),
    reimbursed: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
) -> MemberExpenseListResponse:
    return await expense_service.list_expenses(db, member_id, reimbursed)


@router.patch("/expenses/{expense_id}/reimbursed", response_model=MemberExpenseResponse, summary="Update reimbursement status")
async def update_reimbursed(
    expense_id: uuid.UUID,
    data: MemberExpenseStatusUpdate,
    db: AsyncSession = Depends(get_db),
) -> MemberExpenseResponse:
    try:
        return await expense_service.update_reimbursed(db, expense_id, data.reimbursed)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/expenses/{expense_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete member expense")
async def delete_expense(expense_id: uuid.UUID, db: AsyncSession = Depends(get_db)) -> None:
    try:
        await expense_service.delete_expense(db, expense_id)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
