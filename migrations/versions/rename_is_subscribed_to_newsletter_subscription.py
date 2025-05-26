"""rename is_subscribed to newsletter_subscription

Revision ID: rename_is_subscribed
Revises: 20240423_rename_is_subscribed
Create Date: 2024-04-23 08:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = 'rename_is_subscribed'
down_revision = '20240423_rename_is_subscribed'
branch_labels = None
depends_on = None

def upgrade():
    # Get the inspector to check column existence
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Only rename if is_subscribed exists and newsletter_subscription doesn't
    if 'is_subscribed' in columns and 'newsletter_subscription' not in columns:
        op.alter_column('users', 'is_subscribed', new_column_name='newsletter_subscription')
    elif 'newsletter_subscription' not in columns:
        # If neither column exists, add newsletter_subscription
        op.add_column('users', sa.Column('newsletter_subscription', sa.Boolean(), nullable=True, server_default='1'))

def downgrade():
    # Get the inspector to check column existence
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    # Only rename back if newsletter_subscription exists and is_subscribed doesn't
    if 'newsletter_subscription' in columns and 'is_subscribed' not in columns:
        op.alter_column('users', 'newsletter_subscription', new_column_name='is_subscribed') 