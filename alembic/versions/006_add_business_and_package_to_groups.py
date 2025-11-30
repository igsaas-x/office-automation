"""Add business name and package management to groups table

Revision ID: 006
Revises: 005
Create Date: 2025-11-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add business_name and package management columns to groups table"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    group_columns = [col['name'] for col in inspector.get_columns('groups')]

    # Add business_name column
    if 'business_name' not in group_columns:
        op.add_column('groups', sa.Column('business_name', sa.String(255), nullable=True))

    # Add package_level column with default 'free'
    if 'package_level' not in group_columns:
        op.add_column('groups', sa.Column('package_level', sa.String(20), nullable=False, server_default='free'))

    # Add package_updated_at column
    if 'package_updated_at' not in group_columns:
        op.add_column('groups', sa.Column('package_updated_at', sa.DateTime(), nullable=True))

    # Add package_updated_by column (stores Telegram user ID of admin who updated)
    if 'package_updated_by' not in group_columns:
        op.add_column('groups', sa.Column('package_updated_by', sa.String(255), nullable=True))


def downgrade() -> None:
    """Remove business_name and package management columns from groups table"""
    # Remove columns in reverse order
    op.drop_column('groups', 'package_updated_by')
    op.drop_column('groups', 'package_updated_at')
    op.drop_column('groups', 'package_level')
    op.drop_column('groups', 'business_name')
