"""merge all heads

Revision ID: 90c2bd719b50
Revises: dd7dca2b64bf, fix_circular_dependencies
Create Date: 2025-04-22 18:06:54.052200

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '90c2bd719b50'
down_revision = ('dd7dca2b64bf', 'fix_circular_dependencies')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
