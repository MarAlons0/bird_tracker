"""Add created_at to locations table

Revision ID: 3a4b5c6d7e8f
Revises: 2a3b4c5d6e7f
Create Date: 2024-03-19 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3a4b5c6d7e8f'
down_revision = '2a3b4c5d6e7f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('locations', sa.Column('created_at', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('locations', 'created_at') 