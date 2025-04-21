"""Add Location and UserPreferences tables

Revision ID: 2a3b4c5d6e7f
Revises: 1a2b3c4d5e6f
Create Date: 2024-03-19 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2a3b4c5d6e7f'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade():
    # Create locations table
    op.create_table('locations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('radius', sa.Float(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create user_preferences table
    op.create_table('user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('default_location_id', sa.Integer(), nullable=True),
        sa.Column('notification_enabled', sa.Boolean(), default=True),
        sa.Column('email_frequency', sa.String(length=20), default='daily'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['default_location_id'], ['locations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )


def downgrade():
    op.drop_table('user_preferences')
    op.drop_table('locations') 