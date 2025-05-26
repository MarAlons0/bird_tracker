from app import create_app
from app.models import CarouselImage, db
from datetime import datetime

def init_carousel_images():
    app = create_app()
    with app.app_context():
        # Clear existing carousel images
        CarouselImage.query.delete()
        db.session.commit()
        
        # Sample bird images from Cloudinary
        images = [
            {
                'filename': 'https://res.cloudinary.com/dxgzx3wta/image/upload/v1/bird_tracker/carousel/american_robin.jpg',
                'title': 'American Robin',
                'description': 'A common sight in North American gardens',
                'order': 1,
                'is_active': True
            },
            {
                'filename': 'https://res.cloudinary.com/dxgzx3wta/image/upload/v1/bird_tracker/carousel/blue_jay.jpg',
                'title': 'Blue Jay',
                'description': 'Known for its distinctive blue plumage',
                'order': 2,
                'is_active': True
            },
            {
                'filename': 'https://res.cloudinary.com/dxgzx3wta/image/upload/v1/bird_tracker/carousel/cardinal.jpg',
                'title': 'Northern Cardinal',
                'description': 'The state bird of seven US states',
                'order': 3,
                'is_active': True
            }
        ]
        
        # Add images to database
        for image_data in images:
            image = CarouselImage(**image_data)
            db.session.add(image)
        
        db.session.commit()
        print("Carousel images initialized successfully!")

if __name__ == '__main__':
    init_carousel_images() 