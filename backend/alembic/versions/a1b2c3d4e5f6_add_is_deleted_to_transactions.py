"""add is_deleted to transactions

Revision ID: a1b2c3d4e5f6
Revises: 88423ea5d0cf
Create Date: 2026-05-22 11:12:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '88423ea5d0cf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'transactions',
        sa.Column(
            'is_deleted',
            sa.Boolean(),
            nullable=False,
            server_default=sa.text('FALSE'),
        ),
    )
    op.create_index(
        op.f('ix_transactions_is_deleted'),
        'transactions',
        ['is_deleted'],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_transactions_is_deleted'), table_name='transactions')
    op.drop_column('transactions', 'is_deleted')
