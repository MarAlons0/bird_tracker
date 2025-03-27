from app import app, db
from models import User
import logging
from sqlalchemy import text

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    with app.app_context():
        logger.debug("Creating database tables...")
        try:
            # Drop all existing tables
            db.drop_all()
            logger.debug("Dropped existing tables")
            
            # Create all tables
            db.create_all()
            logger.debug("Created new tables")
            
            # Check if admin user exists
            admin_email = 'alonsoencinci@gmail.com'
            if not User.query.filter_by(email=admin_email).first():
                # Create admin user
                admin = User(
                    email=admin_email,
                    is_approved=True
                )
                db.session.add(admin)
                db.session.commit()
                logger.info(f"Created admin user: {admin_email}")
            else:
                logger.info(f"Admin user already exists: {admin_email}")
                
            # Verify tables were created
            with db.engine.connect() as conn:
                # Use text() to create an executable SQL statement
                sql = text("SELECT name FROM sqlite_master WHERE type='table';")
                tables = conn.execute(sql).fetchall()
                logger.debug(f"Created tables: {[table[0] for table in tables]}")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise

if __name__ == '__main__':
    init_db() 