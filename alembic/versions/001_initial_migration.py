"""Initial migration

Revision ID: 001
Revises:
Create Date: 2025-10-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create employees table
    op.create_table(
        'employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )
    op.create_index(op.f('ix_employees_telegram_id'), 'employees', ['telegram_id'], unique=True)

    # Create check_ins table
    op.create_table(
        'check_ins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_check_ins_employee_id'), 'check_ins', ['employee_id'], unique=False)

    # Create salary_advances table
    op.create_table(
        'salary_advances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('employee_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.String(length=50), nullable=False),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_by', sa.String(length=255), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_salary_advances_employee_id'), 'salary_advances', ['employee_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_salary_advances_employee_id'), table_name='salary_advances')
    op.drop_table('salary_advances')
    op.drop_index(op.f('ix_check_ins_employee_id'), table_name='check_ins')
    op.drop_table('check_ins')
    op.drop_index(op.f('ix_employees_telegram_id'), table_name='employees')
    op.drop_table('employees')
