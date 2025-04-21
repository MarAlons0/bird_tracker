from app import create_app, db
from werkzeug.security import generate_password_hash
from app.models import User, Location, UserPreferences
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_db():
    app = create_app()
    with app.app_context():
        try:
            logger.info("Starting database initialization...")
            
            # Ensure the database directory exists
            db_dir = os.path.dirname(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir)
                logger.info(f"Created database directory: {db_dir}")
            
            logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Drop all tables
            logger.info("Dropping existing tables...")
            db.drop_all()
            
            # Create all tables
            logger.info("Creating new tables...")
            db.create_all()
            logger.info("Database tables created")

            # Create admin user
            admin_email = 'alonsoencinci@gmail.com'
            admin_password = 'admin123'
            
            logger.info("Creating admin user...")
            # Create admin user
            admin = User(
                username=admin_email,  # Use email as username
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True,
                is_approved=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            logger.info("Admin user created")
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Error during database initialization: {str(e)}")
            raise

if __name__ == '__main__':
    init_db() 