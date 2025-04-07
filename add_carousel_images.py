import os
from app import create_app, db
from models import CarouselImage
from werkzeug.utils import secure_filename
from utils.image_processing import process_image, upload_to_cloudinary
from PIL import Image as PILImage
import io

def ensure_carousel_directory():
    """Ensure the carousel directory exists"""
    carousel_dir = os.path.join('static', 'images', 'carousel')
    if not os.path.exists(carousel_dir):
        os.makedirs(carousel_dir)
    return carousel_dir

def add_carousel_images():
    """Add carousel images to the database"""
    app = create_app()
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Ensure carousel directory exists
        carousel_dir = ensure_carousel_directory()
        
        # List of images to add
        images = [
            {'filename': 'photo1.jpg', 'title': 'American Robin', 'description': 'A common sight in North American gardens'},
            {'filename': 'photo2.jpeg', 'title': 'Blue Jay', 'description': 'Known for its distinctive blue plumage'},
            {'filename': 'photo3.jpeg', 'title': 'Cardinal', 'description': 'The state bird of seven US states'},
            {'filename': 'photo4.jpeg', 'title': 'Chickadee', 'description': 'Small, friendly birds with distinctive calls'},
            {'filename': 'photo5.jpeg', 'title': 'Eagle', 'description': 'Majestic birds of prey'},
            {'filename': 'photo6.jpeg', 'title': 'Finch', 'description': 'Small songbirds with colorful plumage'},
            {'filename': 'photo7.jpeg', 'title': 'Goldfinch', 'description': 'Bright yellow songbirds'},
            {'filename': 'photo8.jpeg', 'title': 'Hawk', 'description': 'Skilled hunters of the sky'},
            {'filename': 'photo9.jpeg', 'title': 'Hummingbird', 'description': 'Tiny birds with incredible speed'},
            {'filename': 'photo10.jpeg', 'title': 'Kingfisher', 'description': 'Expert fishers with distinctive calls'},
            {'filename': 'photo11.jpeg', 'title': 'Mockingbird', 'description': 'Known for their ability to mimic other birds'},
            {'filename': 'photo12.jpeg', 'title': 'Nuthatch', 'description': 'Birds that walk headfirst down trees'},
            {'filename': 'photo13.jpeg', 'title': 'Owl', 'description': 'Nocturnal hunters with silent flight'},
            {'filename': 'photo14.jpg', 'title': 'Parrot', 'description': 'Colorful birds known for their intelligence'},
            {'filename': 'photo15.jpg', 'title': 'Pigeon', 'description': 'Common urban birds with surprising intelligence'},
            {'filename': 'photo16.jpeg', 'title': 'Quail', 'description': 'Ground-dwelling birds with distinctive calls'},
            {'filename': 'photo17.jpeg', 'title': 'Raven', 'description': 'Highly intelligent birds of the corvid family'},
            {'filename': 'photo18.jpeg', 'title': 'Sparrow', 'description': 'Small, adaptable songbirds'},
            {'filename': 'photo19.jpeg', 'title': 'Swallow', 'description': 'Agile aerial insectivores'},
            {'filename': 'photo20.jpeg', 'title': 'Woodpecker', 'description': 'Birds that drum on trees for food'}
        ]
        
        # Process each image
        for i, image_data in enumerate(images):
            filename = image_data['filename']
            image_path = os.path.join('static', 'images', 'birds', filename)
            
            try:
                # Open and process the image
                with PILImage.open(image_path) as img:
                    # Convert to RGB if necessary
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Process the image
                    processed_img = process_image(img)
                    
                    # Convert processed image to bytes
                    img_byte_arr = io.BytesIO()
                    processed_img.save(img_byte_arr, format='JPEG')
                    img_byte_arr.seek(0)
                    
                    # Upload to Cloudinary
                    cloudinary_path = f"carousel/{filename}"
                    upload_result = upload_to_cloudinary(img_byte_arr, cloudinary_path)
                    
                    if not upload_result or 'secure_url' not in upload_result:
                        print(f"Warning: Failed to upload {filename} to Cloudinary")
                        continue
                    
                    # Check if image already exists
                    existing = CarouselImage.query.filter_by(filename=filename).first()
                    
                    if existing:
                        # Update existing image
                        existing.cloudinary_url = upload_result['secure_url']
                        existing.title = image_data['title']
                        existing.description = image_data['description']
                        existing.order = i
                        existing.is_active = True
                        print(f"Updated image {filename} with Cloudinary URL: {upload_result['secure_url']}")
                    else:
                        # Create new carousel image
                        image = CarouselImage(
                            filename=filename,
                            cloudinary_url=upload_result['secure_url'],
                            title=image_data['title'],
                            description=image_data['description'],
                            order=i,
                            is_active=True
                        )
                        db.session.add(image)
                        print(f"Added image {filename} to database with Cloudinary URL: {upload_result['secure_url']}")
                
            except Exception as e:
                print(f"Error processing image {filename}: {str(e)}")
                db.session.rollback()
                continue
        
        try:
            db.session.commit()
            print("Successfully committed all changes to database")
        except Exception as e:
            print(f"Error committing to database: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    add_carousel_images() 