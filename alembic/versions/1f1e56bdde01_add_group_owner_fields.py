"""add_group_owner_fields

Revision ID: 1f1e56bdde01
Revises: 009
Create Date: 2025-12-14 16:50:28.879372

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1f1e56bdde01'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add group owner/creator fields to groups table
    op.add_column('groups', sa.Column('created_by_telegram_id', sa.String(255), nullable=True))
    op.add_column('groups', sa.Column('created_by_username', sa.String(255), nullable=True))
    op.add_column('groups', sa.Column('created_by_first_name', sa.String(255), nullable=True))
    op.add_column('groups', sa.Column('created_by_last_name', sa.String(255), nullable=True))

    # Create index on created_by_username for faster searches
    op.create_index('idx_groups_created_by_username', 'groups', ['created_by_username'])


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_groups_created_by_username', table_name='groups')

    # Remove columns
    op.drop_column('groups', 'created_by_last_name')
    op.drop_column('groups', 'created_by_first_name')
    op.drop_column('groups', 'created_by_username')
    op.drop_column('groups', 'created_by_telegram_id')
