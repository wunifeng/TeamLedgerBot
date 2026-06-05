"""add salary payment voiding

Revision ID: e4f5g6h7i8j9
Revises: d1e2f3g4h5i6
Create Date: 2026-06-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision: str = "e4f5g6h7i8j9"
down_revision: Union[str, None] = "d1e2f3g4h5i6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 作废保留原发放记录，但不再计入已付工资。
    op.add_column("salary_payments", sa.Column("voided_at", sa.TIMESTAMP(timezone=True), nullable=True))
    op.add_column("salary_payments", sa.Column("void_reason", sa.Text(), nullable=True))
    op.add_column("salary_payments", sa.Column("voided_by_member_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(
        "fk_salary_payments_voided_by_member_id_members",
        "salary_payments",
        "members",
        ["voided_by_member_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_salary_payments_voided_at"), "salary_payments", ["voided_at"], unique=False)
    op.create_index(
        op.f("ix_salary_payments_voided_by_member_id"),
        "salary_payments",
        ["voided_by_member_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_salary_payments_voided_by_member_id"), table_name="salary_payments")
    op.drop_index(op.f("ix_salary_payments_voided_at"), table_name="salary_payments")
    op.drop_constraint(
        "fk_salary_payments_voided_by_member_id_members",
        "salary_payments",
        type_="foreignkey",
    )
    op.drop_column("salary_payments", "voided_by_member_id")
    op.drop_column("salary_payments", "void_reason")
    op.drop_column("salary_payments", "voided_at")
