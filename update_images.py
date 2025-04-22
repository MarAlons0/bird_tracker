from app import create_app
from app.models import CarouselImage, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_carousel_images():
    """Update Cloudinary URLs for carousel images."""
    try:
        app = create_app()
        with app.app_context():
            # Get all carousel images
            images = CarouselImage.query.all()
            logger.info(f"Found {len(images)} carousel images")
            
            # Update URLs
            for img in images:
                if img.filename == "welcome.jpg":
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/bird_tracker/welcome.jpg"
                elif img.filename == "explore.jpg":
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/bird_tracker/explore.jpg"
                elif img.filename == "share.jpg":
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/bird_tracker/share.jpg"
                
                logger.info(f"Updated image {img.id}: {img.cloudinary_url}")
            
            # Commit changes
            db.session.commit()
            logger.info("Successfully updated carousel image URLs")
            
    except Exception as e:
        logger.error(f"Error updating carousel images: {str(e)}")
        raise

if __name__ == '__main__':
    update_carousel_images() 