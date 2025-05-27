"""merge heads

Revision ID: ab311871e388
Revises: add_created_at_to_users
Create Date: 2025-05-27 08:41:57.929814

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ab311871e388'
down_revision = 'add_created_at_to_users'
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
