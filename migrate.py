import logging
from flask import Flask
from flask_migrate import Migrate
from app.report_app import create_app
from app.models import db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_migrations():
    try:
        logger.info("Creating Flask app...")
        app = create_app()
        
        logger.info("Initializing migrations...")
        migrate = Migrate(app, db)
        
        logger.info("Migrations initialized successfully")
        return app, migrate
    except Exception as e:
        logger.error(f"Error initializing migrations: {str(e)}")
        raise

if __name__ == '__main__':
    try:
        app, migrate = init_migrations()
        
        with app.app_context():
            from flask_migrate import upgrade as _upgrade
            logger.info("Starting database migrations...")
            
            # Log database URL (with password masked)
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            if '@' in db_url:
                masked_url = db_url.split('@')[1]
                logger.info(f"Using database: ...@{masked_url}")
            
            _upgrade()
            logger.info("Database migrations completed successfully!")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise 