import sys
import os
from datetime import datetime
import cloudinary
import cloudinary.api

# Add the current directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from app.models import CarouselImage

def restore_carousel_images():
    with app.app_context():
        # Configure Cloudinary
        cloudinary.config(
            cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
            api_key=os.getenv('CLOUDINARY_API_KEY'),
            api_secret=os.getenv('CLOUDINARY_API_SECRET')
        )
        
        # Get all images from Cloudinary
        result = cloudinary.api.resources(
            type="upload",
            prefix="carousel/",  # Adjust this if your images are in a different folder
            max_results=100
        )
        
        # Clear existing carousel images
        CarouselImage.query.delete()
        
        # Add each image to the database
        for idx, resource in enumerate(result['resources']):
            image = CarouselImage(
                filename=resource['public_id'].split('/')[-1],
                cloudinary_url=resource['secure_url'],
                title=f"Image {idx + 1}",  # Default title
                description="",  # Empty description
                order=idx,
                is_active=True,
                filepath=resource['secure_url'],
                upload_date=datetime.utcnow()
            )
            db.session.add(image)
        
        # Commit changes
        db.session.commit()
        print(f"Restored {len(result['resources'])} carousel images")

if __name__ == '__main__':
    restore_carousel_images() 