"""refactor_to_telegram_users_table

Revision ID: 95b079be95d0
Revises: 1f1e56bdde01
Create Date: 2025-12-14 16:53:57.364017

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '95b079be95d0'
down_revision: Union[str, None] = '1f1e56bdde01'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Step 1: Create telegram_users table
    op.create_table(
        'telegram_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.String(255), nullable=False),
        sa.Column('username', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(255), nullable=True),
        sa.Column('last_name', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )

    # Create indexes
    op.create_index('idx_telegram_users_username', 'telegram_users', ['username'])
    op.create_index('idx_telegram_users_telegram_id', 'telegram_users', ['telegram_id'])

    # Step 2: Migrate existing user data from groups to telegram_users
    connection = op.get_bind()

    # Insert unique users from groups into telegram_users
    connection.execute(sa.text("""
        INSERT INTO telegram_users (telegram_id, username, first_name, last_name, created_at, updated_at)
        SELECT DISTINCT
            created_by_telegram_id,
            created_by_username,
            created_by_first_name,
            created_by_last_name,
            NOW(),
            NOW()
        FROM `groups`
        WHERE created_by_telegram_id IS NOT NULL
        ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            first_name = VALUES(first_name),
            last_name = VALUES(last_name),
            updated_at = NOW()
    """))

    # Step 3: Add created_by_user_id column to groups
    op.add_column('groups', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_groups_created_by_user_id', 'groups', 'telegram_users', ['created_by_user_id'], ['id'])

    # Step 4: Populate created_by_user_id
    connection.execute(sa.text("""
        UPDATE `groups` g
        INNER JOIN telegram_users tu ON g.created_by_telegram_id = tu.telegram_id
        SET g.created_by_user_id = tu.id
        WHERE g.created_by_telegram_id IS NOT NULL
    """))

    # Step 5: Drop old user fields from groups
    op.drop_index('idx_groups_created_by_username', table_name='groups')
    op.drop_column('groups', 'created_by_last_name')
    op.drop_column('groups', 'created_by_first_name')
    op.drop_column('groups', 'created_by_username')
    op.drop_column('groups', 'created_by_telegram_id')


def downgrade() -> None:
    # Re-add old columns
    op.add_column('groups', sa.Column('created_by_telegram_id', sa.String(255), nullable=True))
    op.add_column('groups', sa.Column('created_by_username', sa.String(255), nullable=True))
    op.add_column('groups', sa.Column('created_by_first_name', sa.String(255), nullable=True))
    op.add_column('groups', sa.Column('created_by_last_name', sa.String(255), nullable=True))
    op.create_index('idx_groups_created_by_username', 'groups', ['created_by_username'])

    # Migrate data back
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE `groups` g
        INNER JOIN telegram_users tu ON g.created_by_user_id = tu.id
        SET
            g.created_by_telegram_id = tu.telegram_id,
            g.created_by_username = tu.username,
            g.created_by_first_name = tu.first_name,
            g.created_by_last_name = tu.last_name
        WHERE g.created_by_user_id IS NOT NULL
    """))

    # Drop FK and column
    op.drop_constraint('fk_groups_created_by_user_id', 'groups', type_='foreignkey')
    op.drop_column('groups', 'created_by_user_id')

    # Drop telegram_users table
    op.drop_index('idx_telegram_users_telegram_id', table_name='telegram_users')
    op.drop_index('idx_telegram_users_username', table_name='telegram_users')
    op.drop_table('telegram_users')
