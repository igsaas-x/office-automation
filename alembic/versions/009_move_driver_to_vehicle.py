"""Move driver data to vehicle table

Revision ID: 009
Revises: 008
Create Date: 2025-12-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Move driver name into vehicle table and remove drivers table"""

    # Step 1: Add driver_name column to vehicles table
    op.add_column('vehicles', sa.Column('driver_name', sa.String(100), nullable=True))

    # Step 2: Migrate existing driver data to vehicles
    # Update vehicles with driver names from the drivers table
    op.execute("""
        UPDATE vehicles v
        INNER JOIN drivers d ON d.assigned_vehicle_id = v.id
        SET v.driver_name = d.name
    """)

    # Step 3: Add driver_name column to trips table (for historical snapshot)
    op.add_column('trips', sa.Column('driver_name', sa.String(100), nullable=True))

    # Step 4: Migrate existing driver data to trips
    # Update trips with driver names from the drivers table
    op.execute("""
        UPDATE trips t
        INNER JOIN drivers d ON d.id = t.driver_id
        SET t.driver_name = d.name
    """)

    # Step 5: Drop foreign key constraints from trips and drivers tables
    op.drop_constraint('trips_ibfk_3', 'trips', type_='foreignkey')

    # Step 6: Drop driver_id column from trips
    op.drop_column('trips', 'driver_id')

    # Step 7: Drop foreign key from drivers table
    op.drop_constraint('drivers_ibfk_2', 'drivers', type_='foreignkey')

    # Step 8: Drop the drivers table
    op.drop_table('drivers')


def downgrade() -> None:
    """Restore drivers table (NOTE: This will lose driver assignments and details)"""

    # Recreate drivers table (simplified - will lose historical data)
    op.create_table(
        'drivers',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('group_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('role', sa.String(20), nullable=False, server_default='DRIVER'),
        sa.Column('assigned_vehicle_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['group_id'], ['groups.id'], ),
        sa.ForeignKeyConstraint(['assigned_vehicle_id'], ['vehicles.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('group_id', 'phone', name='uq_group_phone')
    )

    # Add driver_id back to trips
    op.add_column('trips', sa.Column('driver_id', sa.Integer(), nullable=True))

    # Add foreign key constraint back
    op.create_foreign_key('trips_ibfk_3', 'trips', 'drivers', ['driver_id'], ['id'])

    # Remove driver_name from trips
    op.drop_column('trips', 'driver_name')

    # Remove driver_name from vehicles
    op.drop_column('vehicles', 'driver_name')
