from app import create_app
from extensions import db
from models import CarouselImage
import os

def init_carousel_images():
    app = create_app()
    with app.app_context():
        # Clear existing carousel images
        CarouselImage.query.delete()
        
        # List of images to add with their details
        images = [
            {
                'filename': 'photo1.jpg',
                'title': 'Beautiful Bird in Nature',
                'description': 'A stunning capture of a bird in its natural habitat',
                'order': 1,
                'is_active': True
            },
            {
                'filename': 'photo2.jpeg',
                'title': 'Bird in Flight',
                'description': 'Majestic bird soaring through the sky',
                'order': 2,
                'is_active': True
            },
            {
                'filename': 'photo3.jpeg',
                'title': 'Bird Portrait',
                'description': 'Close-up portrait of a beautiful bird',
                'order': 3,
                'is_active': True
            },
            {
                'filename': 'photo4.jpeg',
                'title': 'Bird Watching',
                'description': 'A peaceful moment observing birds in nature',
                'order': 4,
                'is_active': True
            }
        ]
        
        # Add images to database
        for image_data in images:
            # Check if image file exists
            if os.path.exists(f'static/images/birds/{image_data["filename"]}'):
                image = CarouselImage(**image_data)
                db.session.add(image)
        
        db.session.commit()
        print("Carousel images initialized successfully!")

if __name__ == '__main__':
    init_carousel_images() 