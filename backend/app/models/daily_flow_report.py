"""成员每日业务流水与工资计提模型。"""
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, Date, ForeignKey, Index, JSON, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import TIMESTAMP

from app.database import Base

if TYPE_CHECKING:
    from app.models.member import Member
    from app.models.venue import Venue


class DailyFlowReport(Base):
    """保存成员填报的业务流水原始字段。"""

    __tablename__ = "daily_flow_reports"
    __table_args__ = (
        Index(
            "uq_daily_flow_duplicate_active",
            "member_id",
            "business_date",
            "venue_id",
            "profit_loss",
            unique=True,
            postgresql_where=text("is_deleted = FALSE"),
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
        UUID(as_uuid=True), ForeignKey("members.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    venue_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("venues.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    game: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    card_number: Mapped[str] = mapped_column(String(100), nullable=False, default="0", server_default=text("'0'"))
    principal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    chip_code: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    loss_rebate: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    profit_loss: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    remark: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("FALSE"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"), index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()"), onupdate=func.now()
    )

    member: Mapped["Member"] = relationship("Member", back_populates="daily_flow_reports", lazy="joined")
    venue: Mapped["Venue"] = relationship("Venue", back_populates="daily_flow_reports", lazy="joined")
    salary_accrual: Mapped["SalaryAccrual"] = relationship(
        "SalaryAccrual", back_populates="daily_flow_report", uselist=False, lazy="joined"
    )
    change_logs: Mapped[List["FlowChangeLog"]] = relationship(
        "FlowChangeLog", back_populates="flow", lazy="select", cascade="all, delete-orphan"
    )


class SalaryAccrual(Base):
    """保存单条流水对应的工资结果和规则快照。"""

    __tablename__ = "salary_accruals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    daily_flow_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_flow_reports.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    rebate_rate: Mapped[Decimal] = mapped_column(Numeric(5, 3), nullable=False)
    salary_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    rule_description: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False, server_default=text("NOW()")
    )

    daily_flow_report: Mapped["DailyFlowReport"] = relationship(
        "DailyFlowReport", back_populates="salary_accrual", lazy="joined"
    )


class FlowChangeLog(Base):
    """记录每日流水的创建、修改、删除操作历史。"""

    __tablename__ = "flow_change_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    flow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("daily_flow_reports.id", ondelete="CASCADE"),
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

    flow: Mapped["DailyFlowReport"] = relationship(
        "DailyFlowReport", back_populates="change_logs", lazy="select"
    )
    operator: Mapped[Optional["Member"]] = relationship(
        "Member", back_populates="flow_change_logs", lazy="joined"
    )
