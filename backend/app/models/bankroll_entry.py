"""成员 bankroll 资金变动模型。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Date, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base

if TYPE_CHECKING:
    from app.models.member import Member


class BankrollEntry(Base):
    """记录成员手头 bankroll 的不可变资金变动。"""

    __tablename__ = "bankroll_entries"
    __table_args__ = (
        CheckConstraint(
            "entry_type IN ('initial', 'top_up', 'return', 'adjustment')",
            name="ck_bankroll_entries_entry_type",
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_bankroll_entries_amount_positive",
        ),
        CheckConstraint(
            "("
            "entry_type = 'adjustment' "
            "AND adjustment_direction IN ('increase', 'decrease')"
            ") OR ("
            "entry_type <> 'adjustment' "
            "AND adjustment_direction IS NULL"
            ")",
            name="ck_bankroll_entries_adjustment_direction",
        ),
        CheckConstraint(
            "voided_at IS NULL OR (void_reason IS NOT NULL AND length(trim(void_reason)) > 0)",
            name="ck_bankroll_entries_void_reason",
        ),
        Index(
            "uq_bankroll_entries_member_initial_active",
            "member_id",
            unique=True,
            postgresql_where=text("entry_type = 'initial' AND voided_at IS NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    business_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    adjustment_direction: Mapped[str | None] = mapped_column(String(10), nullable=True)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    voided_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        index=True,
    )
    void_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    voided_by_member_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        index=True,
    )

    member: Mapped["Member"] = relationship(
        "Member",
        back_populates="bankroll_entries",
        foreign_keys=[member_id],
        lazy="joined",
    )
    voided_by: Mapped["Member | None"] = relationship(
        "Member",
        back_populates="bankroll_voided_entries",
        foreign_keys=[voided_by_member_id],
        lazy="joined",
    )
