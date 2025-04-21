from app import create_app, db
from werkzeug.security import generate_password_hash
from app.models import User, Location, UserPreferences
import os
import logging
import sys

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def init_db():
    app = create_app()
    with app.app_context():
        try:
            logger.info("Starting database initialization...")
            logger.info(f"Current working directory: {os.getcwd()}")
            logger.info(f"Environment variables: {dict(os.environ)}")
            
            # Log database configuration
            db_uri = app.config['SQLALCHEMY_DATABASE_URI']
            logger.info(f"Database URI: {db_uri}")
            logger.info(f"Database engine: {db.engine}")
            
            # Ensure the database directory exists (for SQLite)
            if db_uri.startswith('sqlite'):
                db_dir = os.path.dirname(db_uri.replace('sqlite:///', ''))
                if db_dir and not os.path.exists(db_dir):
                    os.makedirs(db_dir)
                    logger.info(f"Created database directory: {db_dir}")
            
            # Drop all tables
            logger.info("Dropping existing tables...")
            db.drop_all()
            logger.info("Tables dropped successfully")
            
            # Create all tables
            logger.info("Creating new tables...")
            db.create_all()
            
            # Verify tables were created
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            logger.info(f"Created tables: {tables}")
            
            # Create admin user
            admin_email = 'alonsoencinci@gmail.com'
            admin_password = 'admin123'
            
            logger.info(f"Creating admin user with email: {admin_email}")
            # Create admin user
            admin = User(
                username=admin_email,
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True,
                is_approved=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            # Verify admin user was created
            created_admin = User.query.filter_by(email=admin_email).first()
            logger.info(f"Admin user created successfully: {created_admin is not None}")
            if created_admin:
                logger.info(f"Admin user details: id={created_admin.id}, email={created_admin.email}, is_admin={created_admin.is_admin}")
            
            logger.info("Database initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Error during database initialization: {str(e)}", exc_info=True)
            raise

if __name__ == '__main__':
    init_db() 