"""fix newsletter subscription column

Revision ID: 20240423_fix_newsletter
Revises: rename_is_subscribed
Create Date: 2024-04-23 08:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240423_fix_newsletter'
down_revision = 'rename_is_subscribed'
branch_labels = None
depends_on = None

def upgrade():
    # Check if is_subscribed column exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'is_subscribed' in columns:
        # Rename is_subscribed to newsletter_subscription
        op.alter_column('users', 'is_subscribed', new_column_name='newsletter_subscription')
    elif 'newsletter_subscription' not in columns:
        # Add newsletter_subscription column if neither exists
        op.add_column('users', sa.Column('newsletter_subscription', sa.Boolean(), nullable=True, server_default='1'))
    
    # Set all existing users to subscribed by default
    op.execute("UPDATE users SET newsletter_subscription = 1 WHERE newsletter_subscription IS NULL")

def downgrade():
    # Check if newsletter_subscription column exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'newsletter_subscription' in columns:
        # Rename back to is_subscribed
        op.alter_column('users', 'newsletter_subscription', new_column_name='is_subscribed') 