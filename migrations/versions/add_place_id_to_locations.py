"""add place_id to locations

Revision ID: add_place_id_to_locations
Revises: 
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_place_id_to_locations'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add place_id column to locations table
    op.add_column('locations', sa.Column('place_id', sa.String(255), nullable=True))

def downgrade():
    # Remove place_id column from locations table
    op.drop_column('locations', 'place_id') 