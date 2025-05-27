"""Add created_at to users table

Revision ID: add_created_at_to_users
Revises: 24145bd5aa07
Create Date: 2025-05-27 12:40:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_created_at_to_users'
down_revision = '24145bd5aa07'
branch_labels = None
depends_on = None

def upgrade():
    # Add created_at column with default value
    op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
    
    # Set default value for existing rows
    op.execute("UPDATE users SET created_at = registration_date")
    
    # Make the column non-nullable after setting default values
    op.alter_column('users', 'created_at',
                    existing_type=sa.DateTime(),
                    nullable=False,
                    server_default=sa.text('CURRENT_TIMESTAMP'))

def downgrade():
    op.drop_column('users', 'created_at') 