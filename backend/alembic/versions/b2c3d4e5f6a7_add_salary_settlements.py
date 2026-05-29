"""add salary settlements

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-30 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a7"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
    op.create_index(op.f("ix_salary_settlements_member_id"), "salary_settlements", ["member_id"], unique=False)
    op.create_index(op.f("ix_salary_settlements_period_end"), "salary_settlements", ["period_end"], unique=False)
    op.create_index(op.f("ix_salary_settlements_period_start"), "salary_settlements", ["period_start"], unique=False)
    op.add_column("transactions", sa.Column("salary_settlement_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_transactions_salary_settlement_id"), "transactions", ["salary_settlement_id"], unique=False)
    op.create_foreign_key(
        "fk_transactions_salary_settlement_id_salary_settlements",
        "transactions",
        "salary_settlements",
        ["salary_settlement_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_transactions_salary_settlement_id_salary_settlements",
        "transactions",
        type_="foreignkey",
    )
    op.drop_index(op.f("ix_transactions_salary_settlement_id"), table_name="transactions")
    op.drop_column("transactions", "salary_settlement_id")
    op.drop_index(op.f("ix_salary_settlements_period_start"), table_name="salary_settlements")
    op.drop_index(op.f("ix_salary_settlements_period_end"), table_name="salary_settlements")
    op.drop_index(op.f("ix_salary_settlements_member_id"), table_name="salary_settlements")
    op.drop_table("salary_settlements")
