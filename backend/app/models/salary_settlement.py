"""薪资账期结算模型。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List

from sqlalchemy import Date, ForeignKey, Numeric, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.transaction import Transaction


class SalarySettlement(Base):
    """记录单个成员在一个账期内的应付、已付和未付工资。"""

    __tablename__ = "salary_settlements"
    __table_args__ = (
        UniqueConstraint(
            "member_id",
            "period_start",
            "period_end",
            name="uq_salary_settlement_member_period",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    period_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payable_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        default=Decimal("0"),
        server_default=text("0"),
    )
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("NOW()"),
        onupdate=func.now(),
    )

    member: Mapped["Member"] = relationship(
        "Member", back_populates="salary_settlements", lazy="joined"
    )
    transactions: Mapped[List["Transaction"]] = relationship(
        "Transaction", back_populates="salary_settlement", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<SalarySettlement id={self.id} member_id={self.member_id} "
            f"period={self.period_start}:{self.period_end}>"
        )
