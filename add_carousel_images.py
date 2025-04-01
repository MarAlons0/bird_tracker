from app import create_app
from models import CarouselImage, db
import os

def add_carousel_images():
    app = create_app()
    with app.app_context():
        # Get all images from the birds directory
        image_dir = os.path.join('static', 'images', 'birds')
        images = []
        for file in os.listdir(image_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append(file)
        
        # Sort images to ensure consistent order
        images.sort()
        
        # Add each image to the database
        for index, filename in enumerate(images, 1):
            # Check if image already exists in database
            existing = CarouselImage.query.filter_by(filename=filename).first()
            if not existing:
                image = CarouselImage(
                    filename=filename,
                    title=f'Bird Photo {index}',
                    description=f'Beautiful bird photo {index}',
                    order=index,
                    is_active=True
                )
                db.session.add(image)
        
        db.session.commit()
        print(f"Added {len(images)} images to the carousel database")

if __name__ == '__main__':
    add_carousel_images() 