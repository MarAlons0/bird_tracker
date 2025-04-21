"""add carousel images

Revision ID: add_carousel_images
Revises: 
Create Date: 2024-04-21 02:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_carousel_images'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create carousel_images table
    op.create_table('carousel_images',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('cloudinary_url', sa.String(255), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('order', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('carousel_images') 