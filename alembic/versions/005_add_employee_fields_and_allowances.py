"""Add employee fields and allowances table

Revision ID: 005
Revises: 004
Create Date: 2025-11-16

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to employees table
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    employee_columns = [col['name'] for col in inspector.get_columns('employees')]

    if 'phone' not in employee_columns:
        op.add_column('employees', sa.Column('phone', sa.String(50), nullable=True))

    if 'role' not in employee_columns:
        op.add_column('employees', sa.Column('role', sa.String(100), nullable=True))

    if 'date_start_work' not in employee_columns:
        op.add_column('employees', sa.Column('date_start_work', sa.DateTime(), nullable=True))

    if 'probation_months' not in employee_columns:
        op.add_column('employees', sa.Column('probation_months', sa.Integer(), nullable=True))

    if 'base_salary' not in employee_columns:
        op.add_column('employees', sa.Column('base_salary', sa.Float(), nullable=True))

    if 'bonus' not in employee_columns:
        op.add_column('employees', sa.Column('bonus', sa.Float(), nullable=True))

    # Create allowances table if it doesn't exist
    existing_tables = inspector.get_table_names()

    if 'allowances' not in existing_tables:
        op.create_table(
            'allowances',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('employee_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('allowance_type', sa.String(100), nullable=False),
            sa.Column('note', sa.Text(), nullable=True),
            sa.Column('created_by', sa.String(255), nullable=False),
            sa.Column('timestamp', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['employee_id'], ['employees.id'], ),
            sa.PrimaryKeyConstraint('id')
        )


def downgrade() -> None:
    # Drop allowances table
    op.drop_table('allowances')

    # Remove columns from employees table
    op.drop_column('employees', 'bonus')
    op.drop_column('employees', 'base_salary')
    op.drop_column('employees', 'probation_months')
    op.drop_column('employees', 'date_start_work')
    op.drop_column('employees', 'role')
    op.drop_column('employees', 'phone')
