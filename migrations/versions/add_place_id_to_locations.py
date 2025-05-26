"""add place_id to locations

Revision ID: add_place_id_to_locations
Revises: 
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'add_place_id_to_locations'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Get the inspector to check column existence
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('locations')]
    
    # Only add the column if it doesn't exist
    if 'place_id' not in columns:
        op.add_column('locations', sa.Column('place_id', sa.String(255), nullable=True))

def downgrade():
    # Get the inspector to check column existence
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('locations')]
    
    # Only drop the column if it exists
    if 'place_id' in columns:
        op.drop_column('locations', 'place_id') 