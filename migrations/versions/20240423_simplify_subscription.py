"""simplify subscription system

Revision ID: 20240423_simplify_subscription
Create Date: 2024-04-23 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '20240423_simplify_subscription'
down_revision = '20240423_fix_newsletter'
branch_labels = None
depends_on = None

def upgrade():
    # Get the inspector to check column existence
    inspector = inspect(op.get_bind())
    
    # Drop the newsletter_subscriptions table if it exists
    if 'newsletter_subscriptions' in inspector.get_table_names():
        op.drop_table('newsletter_subscriptions')
    
    # Check if is_active column exists in users table
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'is_active' not in columns:
        # Add is_active column if it doesn't exist
        op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'))
    
    # Set all existing users to active by default
    op.execute("UPDATE users SET is_active = 1 WHERE is_active IS NULL")

def downgrade():
    # Recreate the newsletter_subscriptions table
    op.create_table('newsletter_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('last_sent', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Copy subscription status from users to newsletter_subscriptions
    op.execute("""
        INSERT INTO newsletter_subscriptions (user_id, is_active, created_at)
        SELECT id, is_active, CURRENT_TIMESTAMP
        FROM users
    """) 