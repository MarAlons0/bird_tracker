from app import create_app, db
from werkzeug.security import generate_password_hash
from app.models import User, Location, UserPreferences, CarouselImage
from app.scheduler import init_scheduler
import os
import logging
import sys
from datetime import datetime
from app.utils import setup_logging
from app.tasks import send_weekly_bird_sighting_report
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base

print("Starting script execution...")

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("Logging configured")

# Create Base for SQLAlchemy
Base = declarative_base()

def create_carousel_images(db):
    """Create initial carousel images."""
    try:
        logger.info("Starting carousel image creation...")
        
        # Create first carousel image
        image1 = CarouselImage(
            title="Welcome to Bird Tracker",
            description="Track and share your bird sightings with our community",
            filename="welcome.jpg",
            cloudinary_url="https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/bird_tracker/welcome_bird.jpg",
            is_active=True,
            order=1
        )
        logger.info(f"Created first carousel image: {image1.title}")
        
        # Create second carousel image
        image2 = CarouselImage(
            title="Explore Bird Species",
            description="Discover and learn about different bird species in your area",
            filename="explore.jpg",
            cloudinary_url="https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/bird_tracker/explore_birds.jpg",
            is_active=True,
            order=2
        )
        logger.info(f"Created second carousel image: {image2.title}")
        
        # Create third carousel image
        image3 = CarouselImage(
            title="Share Your Sightings",
            description="Contribute to our growing database of bird sightings",
            filename="share.jpg",
            cloudinary_url="https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/bird_tracker/share_sightings.jpg",
            is_active=True,
            order=3
        )
        logger.info(f"Created third carousel image: {image3.title}")
        
        # Add images to session
        db.session.add(image1)
        db.session.add(image2)
        db.session.add(image3)
        logger.info("Added all carousel images to session")
        
        # Commit the changes
        db.session.commit()
        logger.info("Successfully committed carousel images to database")
        
        # Verify the images were created
        images = CarouselImage.query.all()
        logger.info(f"Total carousel images in database: {len(images)}")
        for img in images:
            logger.info(f"Image: {img.title}, Active: {img.is_active}, Order: {img.order}")
            
    except Exception as e:
        logger.error(f"Error creating carousel images: {str(e)}")
        db.session.rollback()
        raise

def init_db():
    """Initialize the database with required data."""
    try:
        logger.info("Starting database initialization...")
        
        # Create Flask app
        app = create_app()
        logger.info("Application initialized successfully")
        
        # Initialize scheduler
        init_scheduler()
        logger.info("Scheduler initialized successfully")
        
        # Get current working directory
        current_dir = os.getcwd()
        logger.info(f"Current working directory: {current_dir}")
        
        # Log environment variables
        logger.info(f"Environment variables: {dict(os.environ)}")
        
        # Get database URI from environment
        database_url = os.environ.get('DATABASE_URL')
        if database_url and database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        logger.info(f"Database URI: {database_url}")
        
        # Create database engine
        engine = create_engine(database_url)
        logger.info(f"Database engine: {engine}")
        
        with app.app_context():
            # Drop all existing tables
            logger.info("Dropping existing tables...")
            Base.metadata.drop_all(engine)
            logger.info("Tables dropped successfully")
            
            # Create all tables
            logger.info("Creating new tables...")
            Base.metadata.create_all(engine)
            logger.info(f"Created tables: {Base.metadata.tables.keys()}")
            
            # Create carousel images
            logger.info("Creating carousel images...")
            create_carousel_images(db)
            logger.info("Carousel images created successfully")
            
            # Create admin user
            admin_email = os.environ.get('ADMIN_EMAIL')
            admin_password = os.environ.get('ADMIN_PASSWORD')
            logger.info(f"Creating admin user with email: {admin_email}")
            
            if admin_email and admin_password:
                # Extract username from email
                username = admin_email.split('@')[0]
                admin_user = User(
                    username=username,
                    email=admin_email,
                    password_hash=generate_password_hash(admin_password),
                    is_admin=True,
                    is_approved=True
                )
                db.session.add(admin_user)
                db.session.commit()
                logger.info(f"Admin user created successfully: {admin_user.is_admin}")
                logger.info(f"Admin user details: id={admin_user.id}, email={admin_user.email}, username={admin_user.username}, is_admin={admin_user.is_admin}")
            else:
                logger.warning("Admin credentials not found in environment variables")
            
            logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Error during database initialization: {str(e)}")
        raise

if __name__ == '__main__':
    init_db()
    print("Script completed") 