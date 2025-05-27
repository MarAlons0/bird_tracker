"""fix circular dependencies

Revision ID: fix_circular_dependencies
Revises: 2ba95f48081a
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_circular_dependencies'
down_revision = '2ba95f48081a'
branch_labels = None
depends_on = None


def upgrade():
    # Drop existing foreign key constraints
    op.drop_constraint('locations_user_id_fkey', 'locations', type_='foreignkey')
    op.drop_constraint('user_preferences_user_id_fkey', 'user_preferences', type_='foreignkey')
    op.drop_constraint('user_preferences_default_location_id_fkey', 'user_preferences', type_='foreignkey')
    op.drop_constraint('user_preferences_active_location_id_fkey', 'user_preferences', type_='foreignkey')
    
    # Add proper foreign key constraints with ON DELETE CASCADE
    op.create_foreign_key(
        'locations_user_id_fkey',
        'locations', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'user_preferences_user_id_fkey',
        'user_preferences', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'user_preferences_default_location_id_fkey',
        'user_preferences', 'locations',
        ['default_location_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'user_preferences_active_location_id_fkey',
        'user_preferences', 'locations',
        ['active_location_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Fix CarouselImage user_id to be a proper foreign key
    op.alter_column('carousel_images', 'user_id',
        existing_type=sa.INTEGER(),
        nullable=True,
        existing_server_default=sa.text("NULL")
    )
    op.create_foreign_key(
        'carousel_images_user_id_fkey',
        'carousel_images', 'users',
        ['user_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    # Drop the new foreign key constraints
    op.drop_constraint('carousel_images_user_id_fkey', 'carousel_images', type_='foreignkey')
    op.drop_constraint('user_preferences_active_location_id_fkey', 'user_preferences', type_='foreignkey')
    op.drop_constraint('user_preferences_default_location_id_fkey', 'user_preferences', type_='foreignkey')
    op.drop_constraint('user_preferences_user_id_fkey', 'user_preferences', type_='foreignkey')
    op.drop_constraint('locations_user_id_fkey', 'locations', type_='foreignkey')
    
    # Recreate the original foreign key constraints
    op.create_foreign_key(
        'locations_user_id_fkey',
        'locations', 'users',
        ['user_id'], ['id']
    )
    op.create_foreign_key(
        'user_preferences_user_id_fkey',
        'user_preferences', 'users',
        ['user_id'], ['id']
    )
    op.create_foreign_key(
        'user_preferences_default_location_id_fkey',
        'user_preferences', 'locations',
        ['default_location_id'], ['id']
    )
    op.create_foreign_key(
        'user_preferences_active_location_id_fkey',
        'user_preferences', 'locations',
        ['active_location_id'], ['id']
    )
    
    # Revert CarouselImage user_id changes
    op.alter_column('carousel_images', 'user_id',
        existing_type=sa.INTEGER(),
        nullable=False,
        existing_server_default=sa.text("NULL")
    ) 