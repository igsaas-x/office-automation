"""Add photo_url to check_ins

Revision ID: 004
Revises: 003
Create Date: 2025-10-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add photo_url column to check_ins table
    # Check if the column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('check_ins')]

    if 'photo_url' not in columns:
        op.add_column('check_ins',
                      sa.Column('photo_url', sa.String(512), nullable=True))


def downgrade() -> None:
    # Remove photo_url column from check_ins table
    op.drop_column('check_ins', 'photo_url')
