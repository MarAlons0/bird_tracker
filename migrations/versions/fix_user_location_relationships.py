"""fix user location relationships

Revision ID: fix_user_location_relationships
Revises: add_carousel_images
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_user_location_relationships'
down_revision = 'add_carousel_images'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the default_location_id column from users table if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='users' AND column_name='default_location_id'
            ) THEN
                ALTER TABLE users DROP COLUMN default_location_id;
            END IF;
        END
        $$;
    """)

    # Ensure user_preferences table has correct columns
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name='user_preferences' AND column_name='default_location_id'
            ) THEN
                ALTER TABLE user_preferences ADD COLUMN default_location_id INTEGER REFERENCES locations(id);
            END IF;
        END
        $$;
    """)


def downgrade():
    # Add back the default_location_id column to users table
    op.add_column('users', sa.Column('default_location_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'locations', ['default_location_id'], ['id']) 