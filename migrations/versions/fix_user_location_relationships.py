"""fix user location relationships

Revision ID: fix_user_location_relationships
Revises: add_carousel_images
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_user_location_relationships'
down_revision = 'add_carousel_images'
branch_labels = None
depends_on = None


def upgrade():
    # No schema changes needed, just relationship fixes
    pass


def downgrade():
    # No schema changes needed, just relationship fixes
    pass 