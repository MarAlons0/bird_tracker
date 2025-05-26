"""rename is_subscribed to newsletter_subscription

Revision ID: 20240423_rename_is_subscribed
Create Date: 2024-04-23 08:20:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20240423_rename_is_subscribed'
down_revision = 'add_place_id_to_locations'
branch_labels = None
depends_on = None

def upgrade():
    # Get the inspector to check column existence
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'is_subscribed' in columns:
        # If is_subscribed exists, rename it
        op.alter_column('users', 'is_subscribed', new_column_name='newsletter_subscription')
    elif 'newsletter_subscription' not in columns:
        # If neither column exists, add newsletter_subscription
        op.add_column('users', sa.Column('newsletter_subscription', sa.Boolean(), nullable=True, server_default='1'))
        op.execute("UPDATE users SET newsletter_subscription = 1 WHERE newsletter_subscription IS NULL")

def downgrade():
    # Get the inspector to check column existence
    inspector = inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'newsletter_subscription' in columns:
        op.alter_column('users', 'newsletter_subscription', new_column_name='is_subscribed') 