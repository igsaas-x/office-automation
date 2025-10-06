"""Rename telegram_group_id to chat_id

Revision ID: 003
Revises: 002
Create Date: 2025-10-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename column in groups table (MySQL requires existing_type)
    # Check if the column exists before renaming
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('groups')]

    if 'telegram_group_id' in columns:
        op.alter_column('groups', 'telegram_group_id',
                        new_column_name='chat_id',
                        existing_type=sa.String(255),
                        existing_nullable=False)


def downgrade() -> None:
    # Rename column back
    op.alter_column('groups', 'chat_id',
                    new_column_name='telegram_group_id',
                    existing_type=sa.String(255),
                    existing_nullable=False)
