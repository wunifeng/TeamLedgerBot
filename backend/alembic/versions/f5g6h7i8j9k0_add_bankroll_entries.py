"""add bankroll entries

Revision ID: f5g6h7i8j9k0
Revises: e4f5g6h7i8j9, 8611a77fc751
Create Date: 2026-06-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "f5g6h7i8j9k0"
down_revision: Union[str, Sequence[str], None] = ("e4f5g6h7i8j9", "8611a77fc751")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 仅创建 bankroll 资金变动表；现有成员默认余额为 0，不自动生成初始记录。
    op.create_table(
        "bankroll_entries",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("member_id", UUID(as_uuid=True), nullable=False),
        sa.Column("entry_type", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("adjustment_direction", sa.String(length=10), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("voided_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("void_reason", sa.Text(), nullable=True),
        sa.Column("voided_by_member_id", UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.CheckConstraint(
            "entry_type IN ('initial', 'top_up', 'return', 'adjustment')",
            name="ck_bankroll_entries_entry_type",
        ),
        sa.CheckConstraint("amount > 0", name="ck_bankroll_entries_amount_positive"),
        sa.CheckConstraint(
            "("
            "entry_type = 'adjustment' "
            "AND adjustment_direction IN ('increase', 'decrease')"
            ") OR ("
            "entry_type <> 'adjustment' "
            "AND adjustment_direction IS NULL"
            ")",
            name="ck_bankroll_entries_adjustment_direction",
        ),
        sa.CheckConstraint(
            "voided_at IS NULL OR (void_reason IS NOT NULL AND length(trim(void_reason)) > 0)",
            name="ck_bankroll_entries_void_reason",
        ),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["voided_by_member_id"], ["members.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_bankroll_entries_business_date"), "bankroll_entries", ["business_date"], unique=False)
    op.create_index(op.f("ix_bankroll_entries_created_at"), "bankroll_entries", ["created_at"], unique=False)
    op.create_index(op.f("ix_bankroll_entries_entry_type"), "bankroll_entries", ["entry_type"], unique=False)
    op.create_index(op.f("ix_bankroll_entries_member_id"), "bankroll_entries", ["member_id"], unique=False)
    op.create_index(op.f("ix_bankroll_entries_voided_at"), "bankroll_entries", ["voided_at"], unique=False)
    op.create_index(
        op.f("ix_bankroll_entries_voided_by_member_id"),
        "bankroll_entries",
        ["voided_by_member_id"],
        unique=False,
    )
    op.create_index(
        "uq_bankroll_entries_member_initial_active",
        "bankroll_entries",
        ["member_id"],
        unique=True,
        postgresql_where=sa.text("entry_type = 'initial' AND voided_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_bankroll_entries_member_initial_active", table_name="bankroll_entries")
    op.drop_index(op.f("ix_bankroll_entries_voided_by_member_id"), table_name="bankroll_entries")
    op.drop_index(op.f("ix_bankroll_entries_voided_at"), table_name="bankroll_entries")
    op.drop_index(op.f("ix_bankroll_entries_member_id"), table_name="bankroll_entries")
    op.drop_index(op.f("ix_bankroll_entries_entry_type"), table_name="bankroll_entries")
    op.drop_index(op.f("ix_bankroll_entries_created_at"), table_name="bankroll_entries")
    op.drop_index(op.f("ix_bankroll_entries_business_date"), table_name="bankroll_entries")
    op.drop_table("bankroll_entries")
