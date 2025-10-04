"""Add groups and employee_groups tables

Revision ID: 002
Revises: 001
Create Date: 2025-10-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create groups table
    op.create_table(
        'groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chat_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('chat_id')
    )
    op.create_index(op.f('ix_groups_chat_id'), 'groups', ['chat_id'], unique=True)

    # Create employee_groups table
    op.create_table(
        'employee_groups',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('employee_id', 'group_id', name='uq_employee_group')
    )
    op.create_index(op.f('ix_employee_groups_employee_id'), 'employee_groups', ['employee_id'], unique=False)
    op.create_index(op.f('ix_employee_groups_group_id'), 'employee_groups', ['group_id'], unique=False)

    # Add group_id to check_ins table
    op.add_column('check_ins', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_check_ins_group_id', 'check_ins', 'groups', ['group_id'], ['id'])
    op.create_index(op.f('ix_check_ins_group_id'), 'check_ins', ['group_id'], unique=False)


def downgrade() -> None:
    # Remove group_id from check_ins
    op.drop_index(op.f('ix_check_ins_group_id'), table_name='check_ins')
    op.drop_constraint('fk_check_ins_group_id', 'check_ins', type_='foreignkey')
    op.drop_column('check_ins', 'group_id')

    # Drop employee_groups table
    op.drop_index(op.f('ix_employee_groups_group_id'), table_name='employee_groups')
    op.drop_index(op.f('ix_employee_groups_employee_id'), table_name='employee_groups')
    op.drop_table('employee_groups')

    # Drop groups table
    op.drop_index(op.f('ix_groups_chat_id'), table_name='groups')
    op.drop_table('groups')
