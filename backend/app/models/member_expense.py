"""成员垫付支出模型。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP, JSON

from app.database import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.member import Member


class MemberExpense(Base):
    """记录成员替团队支付的费用和报销状态。"""

    __tablename__ = "member_expenses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    business_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="SET NULL"), nullable=True, index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    reimbursed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE"), index=True
    )
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"), onupdate=func.now()
    )

    member: Mapped["Member"] = relationship("Member", back_populates="expenses", lazy="joined")
    category: Mapped["Category | None"] = relationship("Category", back_populates="expenses", lazy="joined")
    change_logs: Mapped[List["ExpenseChangeLog"]] = relationship(
        "ExpenseChangeLog", back_populates="expense", lazy="select", cascade="all, delete-orphan"
    )


class ExpenseChangeLog(Base):
    """记录支出记录的创建、修改、删除操作历史。"""

    __tablename__ = "expense_change_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    expense_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("member_expenses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    changed_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"), index=True
    )
    operator_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
    )
    operator_name: Mapped[str] = mapped_column(Text, nullable=False)
    change_type: Mapped[str] = mapped_column(String(20), nullable=False)  # create | update | delete
    before_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    after_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    expense: Mapped["MemberExpense"] = relationship(
        "MemberExpense", back_populates="change_logs", lazy="select"
    )
    operator: Mapped[Optional["Member"]] = relationship(
        "Member", back_populates="expense_change_logs", lazy="joined"
    )
