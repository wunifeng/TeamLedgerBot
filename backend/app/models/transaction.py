"""Transaction ORM model — unified income / expense / salary record."""
import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base
from app.enums import TransactionType

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.member import Member
    from app.models.salary_settlement import SalarySettlement


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    type: Mapped[TransactionType] = mapped_column(
        String(10), nullable=False, index=True
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False
    )
    # Optional for salary type (salary has no category)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    salary_settlement_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("salary_settlements.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    remark: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Only used for salary type
    bonus: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        index=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=func.now(),
    )
    # Soft-delete flag — records are never physically removed
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE"), index=True
    )

    # ── Relationships ─────────────────────────────────────────
    member: Mapped["Member"] = relationship(
        "Member", back_populates="transactions", lazy="joined"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="transactions", lazy="joined"
    )
    salary_settlement: Mapped[Optional["SalarySettlement"]] = relationship(
        "SalarySettlement", back_populates="transactions", lazy="joined"
    )

    def __repr__(self) -> str:
        return (
            f"<Transaction id={self.id} type={self.type} amount={self.amount}>"
        )
