"""成员垫付支出服务。"""
import uuid
from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.category import Category
from app.models.member import Member
from app.models.member_expense import MemberExpense
from app.schemas.expense import MemberExpenseListResponse, MemberExpenseResponse

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


async def create_expense(
    session: AsyncSession,
    business_date: date,
    member_id: uuid.UUID,
    amount: Decimal,
    category_id: Optional[uuid.UUID],
    remark: Optional[str],
    receipt_url: Optional[str],
) -> MemberExpenseResponse:
    """新增成员垫付支出。"""

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
    return _to_response(await _load_expense(session, expense.id))


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


async def delete_expense(session: AsyncSession, expense_id: uuid.UUID) -> None:
    """软删除支出记录。"""

    expense = await _load_expense(session, expense_id)
    if expense.is_deleted:
        raise LookupError(f"支出 {expense_id} 不存在或已删除。")
    expense.is_deleted = True
    await session.flush()
