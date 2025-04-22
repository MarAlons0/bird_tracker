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
            
            # Update URLs with the correct images
            for i, img in enumerate(images):
                if i == 0:
                    img.filename = "Wood_duck_20250405_024922.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821362/carousel/Wood_duck_20250405_024922.jpg"
                    img.title = "Wood Duck"
                elif i == 1:
                    img.filename = "Wild_turkey_20250405_024827.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821307/carousel/Wild_turkey_20250405_024827.jpg"
                    img.title = "Wild Turkey"
                elif i == 2:
                    img.filename = "Turkey_vulture_20250405_024641.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821201/carousel/Turkey_vulture_20250405_024641.jpg"
                    img.title = "Turkey Vulture"
                elif i == 3:
                    img.filename = "Tree_swallow_20250405_024527.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821127/carousel/Tree_swallow_20250405_024527.jpg"
                    img.title = "Tree Swallow"
                elif i == 4:
                    img.filename = "Wood_duck_20250405_024922.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821362/carousel/Wood_duck_20250405_024922.jpg"
                    img.title = "Wood Duck"
                elif i == 5:
                    img.filename = "Wild_turkey_20250405_024827.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821307/carousel/Wild_turkey_20250405_024827.jpg"
                    img.title = "Wild Turkey"
                elif i == 6:
                    img.filename = "Turkey_vulture_20250405_024641.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821201/carousel/Turkey_vulture_20250405_024641.jpg"
                    img.title = "Turkey Vulture"
                elif i == 7:
                    img.filename = "Tree_swallow_20250405_024527.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821127/carousel/Tree_swallow_20250405_024527.jpg"
                    img.title = "Tree Swallow"
                elif i == 8:
                    img.filename = "Wood_duck_20250405_024922.jpg"
                    img.cloudinary_url = "https://res.cloudinary.com/dov36rgse/image/upload/v1743821362/carousel/Wood_duck_20250405_024922.jpg"
                    img.title = "Wood Duck"
                
                logger.info(f"Updated image {img.id}: {img.cloudinary_url}")
            
            # Commit changes
            db.session.commit()
            logger.info("Successfully updated carousel image URLs")
            
    except Exception as e:
        logger.error(f"Error updating carousel images: {str(e)}")
        raise

if __name__ == '__main__':
    update_carousel_images() 