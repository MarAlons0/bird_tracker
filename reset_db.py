from app import create_app, db
from flask_migrate import upgrade
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    app = create_app()
    with app.app_context():
        try:
            logger.info("Dropping all tables...")
            db.drop_all()
            logger.info("Creating fresh tables...")
            db.create_all()
            logger.info("Applying migrations...")
            upgrade()
            logger.info("Database reset and migrations applied successfully!")
        except Exception as e:
            logger.error(f"Error during database reset: {str(e)}")
            raise

if __name__ == '__main__':
    reset_database() 