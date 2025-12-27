"""add_type_to_check_ins

Revision ID: ff935b13936e
Revises: 95b079be95d0
Create Date: 2025-12-27 11:03:01.949779

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ff935b13936e'
down_revision: Union[str, None] = '95b079be95d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add type column to check_ins table
    # Default to 'checkin' for backward compatibility with existing records
    op.add_column('check_ins', sa.Column('type', sa.String(length=20), nullable=False, server_default='checkin'))


def downgrade() -> None:
    # Remove type column from check_ins table
    op.drop_column('check_ins', 'type')
