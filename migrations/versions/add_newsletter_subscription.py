"""add newsletter subscription

Revision ID: add_newsletter_subscription
Revises: 85683a6bb3a7
Create Date: 2024-04-19 09:36:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_newsletter_subscription'
down_revision = '85683a6bb3a7'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('newsletter_subscriptions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_sent', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_newsletter_subscriptions_user_id', 'newsletter_subscriptions', ['user_id'], unique=True)

def downgrade():
    op.drop_index('ix_newsletter_subscriptions_user_id', table_name='newsletter_subscriptions')
    op.drop_table('newsletter_subscriptions') 