"""add updated_at to transactions

Revision ID: a7b3c4d5e6f7
Revises: f04198e3abcb
Create Date: 2026-02-09 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a7b3c4d5e6f7'
down_revision: Union[str, None] = 'f04198e3abcb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add updated_at column to transactions table
    op.add_column('transactions',
        sa.Column('updated_at', sa.DateTime(), nullable=True))

    # Set existing records' updated_at to created_at for consistency
    op.execute('UPDATE transactions SET updated_at = created_at')


def downgrade() -> None:
    # Remove updated_at column
    op.drop_column('transactions', 'updated_at')
