"""add registration requests and carousel images

Revision ID: add_registration_requests_and_carousel_images
Revises: previous_revision
Create Date: 2024-04-21 13:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_registration_requests_and_carousel_images'
down_revision = 'previous_revision'
branch_labels = None
depends_on = None

def upgrade():
    # Create registration_requests table
    op.create_table('registration_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='pending'),
        sa.Column('request_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('processed_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['processed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    
    # Create carousel_images table
    op.create_table('carousel_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('image_url', sa.String(length=500), nullable=False),
        sa.Column('title', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('carousel_images')
    op.drop_table('registration_requests') 