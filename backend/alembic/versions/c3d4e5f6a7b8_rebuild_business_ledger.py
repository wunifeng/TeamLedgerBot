"""rebuild business ledger

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 旧交易数据不再符合业务语义，按产品决策直接移除。
    op.drop_constraint(
        "fk_transactions_salary_settlement_id_salary_settlements",
        "transactions",
        type_="foreignkey",
    )
    op.drop_table("transactions")
    op.drop_table("salary_settlements")

    op.create_table(
        "venues",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("rebate_rate", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("TRUE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index(op.f("ix_venues_name"), "venues", ["name"], unique=True)

    op.create_table(
        "daily_flow_reports",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("venue_id", sa.UUID(), nullable=False),
        sa.Column("game", sa.String(length=50), nullable=False),
        sa.Column("card_number", sa.String(length=100), server_default=sa.text("'0'"), nullable=False),
        sa.Column("principal", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("chip_code", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("loss_rebate", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("profit_loss", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["venue_id"], ["venues.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_daily_flow_reports_business_date"), "daily_flow_reports", ["business_date"], unique=False)
    op.create_index(op.f("ix_daily_flow_reports_created_at"), "daily_flow_reports", ["created_at"], unique=False)
    op.create_index(op.f("ix_daily_flow_reports_game"), "daily_flow_reports", ["game"], unique=False)
    op.create_index(op.f("ix_daily_flow_reports_is_deleted"), "daily_flow_reports", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_daily_flow_reports_member_id"), "daily_flow_reports", ["member_id"], unique=False)
    op.create_index(op.f("ix_daily_flow_reports_venue_id"), "daily_flow_reports", ["venue_id"], unique=False)
    op.create_index(
        "uq_daily_flow_duplicate_active",
        "daily_flow_reports",
        ["member_id", "business_date", "venue_id", "profit_loss"],
        unique=True,
        postgresql_where=sa.text("is_deleted = FALSE"),
    )

    op.create_table(
        "salary_accruals",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("daily_flow_report_id", sa.UUID(), nullable=False),
        sa.Column("rebate_rate", sa.Numeric(precision=5, scale=3), nullable=False),
        sa.Column("salary_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("rule_description", sa.String(length=255), nullable=False),
        sa.Column("rule_snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["daily_flow_report_id"], ["daily_flow_reports.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_salary_accruals_daily_flow_report_id"), "salary_accruals", ["daily_flow_report_id"], unique=True)

    op.create_table(
        "member_expenses",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("business_date", sa.Date(), nullable=False),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("receipt_url", sa.String(length=500), nullable=True),
        sa.Column("reimbursed", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_member_expenses_business_date"), "member_expenses", ["business_date"], unique=False)
    op.create_index(op.f("ix_member_expenses_category_id"), "member_expenses", ["category_id"], unique=False)
    op.create_index(op.f("ix_member_expenses_created_at"), "member_expenses", ["created_at"], unique=False)
    op.create_index(op.f("ix_member_expenses_is_deleted"), "member_expenses", ["is_deleted"], unique=False)
    op.create_index(op.f("ix_member_expenses_member_id"), "member_expenses", ["member_id"], unique=False)
    op.create_index(op.f("ix_member_expenses_reimbursed"), "member_expenses", ["reimbursed"], unique=False)

    op.create_table(
        "salary_settlements",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id", "period_start", "period_end", name="uq_salary_settlement_member_period"),
    )
    op.create_index(op.f("ix_salary_settlements_member_id"), "salary_settlements", ["member_id"], unique=False)
    op.create_index(op.f("ix_salary_settlements_period_end"), "salary_settlements", ["period_end"], unique=False)
    op.create_index(op.f("ix_salary_settlements_period_start"), "salary_settlements", ["period_start"], unique=False)

    op.create_table(
        "salary_payments",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("settlement_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("paid_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["settlement_id"], ["salary_settlements.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_salary_payments_paid_at"), "salary_payments", ["paid_at"], unique=False)
    op.create_index(op.f("ix_salary_payments_settlement_id"), "salary_payments", ["settlement_id"], unique=False)


def downgrade() -> None:
    op.drop_table("salary_payments")
    op.drop_table("salary_settlements")
    op.drop_table("member_expenses")
    op.drop_table("salary_accruals")
    op.drop_table("daily_flow_reports")
    op.drop_table("venues")

    op.create_table(
        "salary_settlements",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("payable_amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(precision=12, scale=2), server_default=sa.text("0"), nullable=False),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("member_id", "period_start", "period_end", name="uq_salary_settlement_member_period"),
    )
    op.create_table(
        "transactions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("type", sa.String(length=10), nullable=False),
        sa.Column("amount", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("salary_settlement_id", sa.UUID(), nullable=True),
        sa.Column("remark", sa.Text(), nullable=True),
        sa.Column("bonus", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("FALSE"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["member_id"], ["members.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["salary_settlement_id"], ["salary_settlements.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
