"""Member ORM model — represents a team member."""
import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base

if TYPE_CHECKING:
    from app.models.daily_flow_report import DailyFlowReport, FlowChangeLog
    from app.models.member_expense import MemberExpense, ExpenseChangeLog
    from app.models.salary_settlement import SalarySettlement


class Member(Base):
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("TRUE")
    )
    # ── 认证字段 ────────────────────────────────────────────────
    pin_hash: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE")
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )

    # ── Relationships ─────────────────────────────────────────
    daily_flow_reports: Mapped[List["DailyFlowReport"]] = relationship(
        "DailyFlowReport", back_populates="member", lazy="select"
    )
    expenses: Mapped[List["MemberExpense"]] = relationship(
        "MemberExpense", back_populates="member", lazy="select"
    )
    salary_settlements: Mapped[List["SalarySettlement"]] = relationship(
        "SalarySettlement", back_populates="member", lazy="select"
    )
    flow_change_logs: Mapped[List["FlowChangeLog"]] = relationship(
        "FlowChangeLog", back_populates="operator", lazy="select"
    )
    expense_change_logs: Mapped[List["ExpenseChangeLog"]] = relationship(
        "ExpenseChangeLog", back_populates="operator", lazy="select"
    )

    def __repr__(self) -> str:
        return f"<Member id={self.id} name={self.name!r}>"
