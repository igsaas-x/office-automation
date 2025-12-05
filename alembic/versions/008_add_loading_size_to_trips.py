"""Add loading_size_cubic_meters to trips

Revision ID: 008
Revises: 007
Create Date: 2025-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add loading_size_cubic_meters column to trips table"""
    op.add_column('trips', sa.Column('loading_size_cubic_meters', sa.Float(), nullable=True))


def downgrade() -> None:
    """Remove loading_size_cubic_meters column from trips table"""
    op.drop_column('trips', 'loading_size_cubic_meters')
