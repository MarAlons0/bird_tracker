from app import create_app, db
from models import Location, UserPreferences
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_locations():
    app = create_app()
    with app.app_context():
        try:
            # Start transaction
            logger.info("Starting location migration...")
            
            # Add user_id column if it doesn't exist
            logger.info("Adding user_id column to locations table...")
            db.session.execute('ALTER TABLE locations ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id)')
            
            # Get all active user preferences
            logger.info("Getting active user preferences...")
            user_prefs = UserPreferences.query.filter_by(is_active=True).all()
            
            # Associate locations with users based on user preferences
            logger.info("Associating locations with users...")
            for pref in user_prefs:
                if pref.location_id:
                    location = Location.query.get(pref.location_id)
                    if location:
                        location.user_id = pref.user_id
                        logger.info(f"Associated location {location.name} with user {pref.user_id}")
            
            # Commit changes
            db.session.commit()
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    migrate_locations() 