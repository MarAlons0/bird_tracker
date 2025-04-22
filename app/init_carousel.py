from app import create_app, db
from app.models import CarouselImage
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_carousel_images():
    """Initialize carousel images in the database."""
    app = create_app()
    with app.app_context():
        try:
            # Clear existing carousel images
            CarouselImage.query.delete()
            db.session.commit()
            logger.info("Cleared existing carousel images")
            
            # Sample carousel images
            images = [
                {
                    'filename': 'https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/carousel/welcome.jpg',
                    'cloudinary_url': 'https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/carousel/welcome.jpg',
                    'title': 'Welcome to Bird Tracker',
                    'description': 'Track and share your bird sightings with our community',
                    'order': 1,
                    'is_active': True
                },
                {
                    'filename': 'https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/carousel/explore.jpg',
                    'cloudinary_url': 'https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/carousel/explore.jpg',
                    'title': 'Explore Bird Species',
                    'description': 'Discover and learn about different bird species in your area',
                    'order': 2,
                    'is_active': True
                },
                {
                    'filename': 'https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/carousel/share.jpg',
                    'cloudinary_url': 'https://res.cloudinary.com/dov36rgse/image/upload/v1713750000/carousel/share.jpg',
                    'title': 'Share Your Sightings',
                    'description': 'Contribute to our growing database of bird sightings',
                    'order': 3,
                    'is_active': True
                }
            ]
            
            logger.info(f"Preparing to create {len(images)} carousel images")
            
            # Add images to database
            for i, image_data in enumerate(images, 1):
                try:
                    logger.info(f"Creating carousel image {i}/{len(images)}: {image_data['title']}")
                    image = CarouselImage(**image_data)
                    db.session.add(image)
                    logger.info(f"Successfully added carousel image to session: {image.title}")
                except Exception as e:
                    logger.error(f"Error creating carousel image {image_data['title']}: {str(e)}", exc_info=True)
                    db.session.rollback()
                    continue
            
            try:
                logger.info("Attempting to commit carousel images to database...")
                db.session.commit()
                
                # Verify carousel images were created
                created_images = CarouselImage.query.all()
                logger.info(f"Successfully created {len(created_images)} carousel images")
                for img in created_images:
                    logger.info(f"Created image: id={img.id}, title={img.title}, filename={img.filename}")
            except Exception as e:
                logger.error(f"Error committing carousel images to database: {str(e)}", exc_info=True)
                db.session.rollback()
                raise
            
            logger.info("Carousel images initialized successfully!")
            
        except Exception as e:
            logger.error(f"Error during carousel image initialization: {str(e)}", exc_info=True)
            raise

if __name__ == '__main__':
    init_carousel_images() 