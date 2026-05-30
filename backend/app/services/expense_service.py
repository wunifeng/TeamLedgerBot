"""成员垫付支出服务。"""
import uuid
from datetime import date
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status as http_status
from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.member import Member
from app.models.member_expense import ExpenseChangeLog, MemberExpense
from app.schemas.expense import (
    ExpenseChangeLogResponse,
    MemberExpenseListResponse,
    MemberExpenseResponse,
    MemberExpenseUpdate,
)

_ZERO = Decimal("0")


def _to_response(expense: MemberExpense) -> MemberExpenseResponse:
    return MemberExpenseResponse(
        id=expense.id,
        business_date=expense.business_date,
        member_id=expense.member_id,
        member_name=expense.member.name,
        category_id=expense.category_id,
        category_name=expense.category.name if expense.category else None,
        amount=expense.amount,
        remark=expense.remark,
        receipt_url=expense.receipt_url,
        reimbursed=expense.reimbursed,
        created_at=expense.created_at,
        updated_at=expense.updated_at,
    )


async def _load_expense(session: AsyncSession, expense_id: uuid.UUID) -> MemberExpense:
    stmt = (
        select(MemberExpense)
        .options(selectinload(MemberExpense.member), selectinload(MemberExpense.category))
        .where(MemberExpense.id == expense_id)
    )
    return (await session.execute(stmt)).scalar_one()


def _expense_snapshot(expense: MemberExpense) -> dict:
    """序列化支出核心字段为 JSON 快照。"""
    return {
        "amount": str(expense.amount),
        "category_id": str(expense.category_id) if expense.category_id else None,
        "category_name": expense.category.name if expense.category else None,
        "remark": expense.remark,
    }


def _write_change_log(
    session: AsyncSession,
    expense: MemberExpense,
    change_type: str,
    operator: Member,
    before_data: Optional[dict] = None,
    after_data: Optional[dict] = None,
) -> None:
    log = ExpenseChangeLog(
        expense_id=expense.id,
        operator_id=operator.id,
        operator_name=operator.name,
        change_type=change_type,
        before_data=before_data,
        after_data=after_data,
    )
    session.add(log)


async def create_expense(
    session: AsyncSession,
    business_date: date,
    member_id: uuid.UUID,
    amount: Decimal,
    category_id: Optional[uuid.UUID],
    remark: Optional[str],
    receipt_url: Optional[str],
    operator: Member,
) -> MemberExpenseResponse:
    """新增成员垫付支出，记录创建日志。"""

    member = await session.get(Member, member_id)
    if member is None or not member.is_active:
        raise LookupError(f"成员 {member_id} 不存在或已停用。")
    if category_id:
        category = await session.get(Category, category_id)
        if category is None or not category.is_active or category.type != "expense":
            raise LookupError(f"支出分类 {category_id} 不存在或已停用。")
    expense = MemberExpense(
        business_date=business_date,
        member_id=member_id,
        amount=amount,
        category_id=category_id,
        remark=remark,
        receipt_url=receipt_url,
    )
    session.add(expense)
    await session.flush()

    loaded = await _load_expense(session, expense.id)
    _write_change_log(
        session, loaded, change_type="create", operator=operator,
        before_data=None, after_data=_expense_snapshot(loaded),
    )
    await session.flush()
    return _to_response(loaded)


async def update_expense(
    session: AsyncSession,
    expense_id: uuid.UUID,
    data: MemberExpenseUpdate,
    operator: Member,
) -> MemberExpenseResponse:
    """修改支出字段，记录变更日志。"""

    expense = await _load_expense(session, expense_id)
    if expense.is_deleted:
        raise LookupError(f"支出 {expense_id} 不存在或已删除。")

    # 权限检查
    if not operator.is_admin and operator.id != expense.member_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="无权限：只能修改自己的支出",
        )

    before = _expense_snapshot(expense)

    update_dict = data.model_dump(exclude_unset=True)
    if not update_dict:
        # 没有任何字段被修改，直接返回
        return _to_response(expense)

    # 校验分类
    new_category_id = update_dict.get("category_id", expense.category_id)
    if new_category_id and new_category_id != expense.category_id:
        category = await session.get(Category, new_category_id)
        if category is None or not category.is_active or category.type != "expense":
            raise LookupError(f"支出分类 {new_category_id} 不存在或已停用。")

    for field, value in update_dict.items():
        setattr(expense, field, value)

    await session.flush()
    loaded = await _load_expense(session, expense.id)
    after = _expense_snapshot(loaded)

    _write_change_log(
        session, loaded, change_type="update", operator=operator,
        before_data=before, after_data=after,
    )
    await session.flush()
    return _to_response(loaded)


async def list_expenses(
    session: AsyncSession,
    member_id: Optional[uuid.UUID] = None,
    reimbursed: Optional[bool] = None,
) -> MemberExpenseListResponse:
    """返回成员垫付支出及汇总。"""

    filters = [MemberExpense.is_deleted.is_(False)]
    if member_id:
        filters.append(MemberExpense.member_id == member_id)
    if reimbursed is not None:
        filters.append(MemberExpense.reimbursed.is_(reimbursed))
    rows = (
        await session.execute(
            select(MemberExpense)
            .options(selectinload(MemberExpense.member), selectinload(MemberExpense.category))
            .where(and_(*filters))
            .order_by(desc(MemberExpense.business_date), desc(MemberExpense.created_at))
        )
    ).scalars().all()
    return MemberExpenseListResponse(
        items=[_to_response(row) for row in rows],
        total_amount=sum((row.amount for row in rows), _ZERO),
        total_unreimbursed=sum((row.amount for row in rows if not row.reimbursed), _ZERO),
    )


async def update_reimbursed(
    session: AsyncSession,
    expense_id: uuid.UUID,
    reimbursed: bool,
) -> MemberExpenseResponse:
    """更新支出的报销状态。"""

    expense = await _load_expense(session, expense_id)
    if expense.is_deleted:
        raise LookupError(f"支出 {expense_id} 不存在或已删除。")
    expense.reimbursed = reimbursed
    await session.flush()
    return _to_response(await _load_expense(session, expense.id))


async def attach_receipt(
    session: AsyncSession,
    expense_id: uuid.UUID,
    receipt_url: str,
) -> MemberExpenseResponse:
    """在业务字段校验通过后关联已上传的凭证。"""

    expense = await _load_expense(session, expense_id)
    expense.receipt_url = receipt_url
    await session.flush()
    return _to_response(await _load_expense(session, expense.id))


async def delete_expense(
    session: AsyncSession, expense_id: uuid.UUID, operator: Member
) -> dict:
    """软删除支出记录，记录删除日志，返回删除前快照（用于 Telegram 通知）。"""

    expense = await _load_expense(session, expense_id)
    if expense.is_deleted:
        raise LookupError(f"支出 {expense_id} 不存在或已删除。")

    # 权限检查
    if not operator.is_admin and operator.id != expense.member_id:
        raise HTTPException(
            status_code=http_status.HTTP_403_FORBIDDEN,
            detail="无权限：只能删除自己的支出",
        )

    before = _expense_snapshot(expense)
    member_name = expense.member.name

    _write_change_log(
        session, expense, change_type="delete", operator=operator,
        before_data=before, after_data=None,
    )
    expense.is_deleted = True
    await session.flush()

    return {
        "member_name": member_name,
        "amount": before["amount"],
        "category_name": before.get("category_name"),
        "remark": before.get("remark"),
    }


async def get_expense_history(
    session: AsyncSession, expense_id: uuid.UUID
) -> List[ExpenseChangeLogResponse]:
    """返回某条支出的完整变更历史，按时间升序。"""
    rows = (
        await session.execute(
            select(ExpenseChangeLog)
            .where(ExpenseChangeLog.expense_id == expense_id)
            .order_by(ExpenseChangeLog.changed_at)
        )
    ).scalars().all()
    return [
        ExpenseChangeLogResponse(
            id=row.id,
            expense_id=row.expense_id,
            changed_at=row.changed_at,
            operator_name=row.operator_name,
            change_type=row.change_type,
            before_data=row.before_data,
            after_data=row.after_data,
        )
        for row in rows
    ]
