"""add auth and change logs

Revision ID: d1e2f3g4h5i6
Revises: c3d4e5f6a7b8
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "d1e2f3g4h5i6"
down_revision: Union[str, None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 扩展 members 表 ────────────────────────────────────────
    op.add_column("members", sa.Column("pin_hash", sa.Text(), nullable=True))
    op.add_column(
        "members",
        sa.Column(
            "is_admin",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("FALSE"),
        ),
    )

    # ── 流水变更日志表 ─────────────────────────────────────────
    op.create_table(
        "flow_change_logs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("flow_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "changed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("operator_id", UUID(as_uuid=True), nullable=True),
        sa.Column("operator_name", sa.Text(), nullable=False),
        sa.Column("change_type", sa.String(length=20), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["flow_id"],
            ["daily_flow_reports.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["operator_id"],
            ["members.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_flow_change_logs_flow_id", "flow_change_logs", ["flow_id"], unique=False
    )
    op.create_index(
        "ix_flow_change_logs_changed_at",
        "flow_change_logs",
        ["changed_at"],
        unique=False,
    )

    # ── 支出变更日志表 ─────────────────────────────────────────
    op.create_table(
        "expense_change_logs",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("expense_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "changed_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.Column("operator_id", UUID(as_uuid=True), nullable=True),
        sa.Column("operator_name", sa.Text(), nullable=False),
        sa.Column("change_type", sa.String(length=20), nullable=False),
        sa.Column("before_data", sa.JSON(), nullable=True),
        sa.Column("after_data", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(
            ["expense_id"],
            ["member_expenses.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["operator_id"],
            ["members.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_expense_change_logs_expense_id",
        "expense_change_logs",
        ["expense_id"],
        unique=False,
    )
    op.create_index(
        "ix_expense_change_logs_changed_at",
        "expense_change_logs",
        ["changed_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_expense_change_logs_changed_at", table_name="expense_change_logs")
    op.drop_index(
        "ix_expense_change_logs_expense_id", table_name="expense_change_logs"
    )
    op.drop_table("expense_change_logs")

    op.drop_index("ix_flow_change_logs_changed_at", table_name="flow_change_logs")
    op.drop_index("ix_flow_change_logs_flow_id", table_name="flow_change_logs")
    op.drop_table("flow_change_logs")

    op.drop_column("members", "is_admin")
    op.drop_column("members", "pin_hash")
