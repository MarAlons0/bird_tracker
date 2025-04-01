import os
from app import create_app
from models import CarouselImage
from werkzeug.utils import secure_filename

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
            {'filename': 'photo15.jpg', 'title': 'Pigeon', 'description': 'Common city dwellers with remarkable navigation'},
            {'filename': 'photo16.jpeg', 'title': 'Quail', 'description': 'Ground-dwelling birds with distinctive calls'},
            {'filename': 'photo17.jpeg', 'title': 'Raven', 'description': 'Highly intelligent corvids'},
            {'filename': 'photo18.jpeg', 'title': 'Sparrow', 'description': 'Small, adaptable songbirds'},
            {'filename': 'photo19.jpeg', 'title': 'Swallow', 'description': 'Graceful aerial acrobats'},
            {'filename': 'photo20.jpeg', 'title': 'Woodpecker', 'description': 'Birds that drum on trees'}
        ]
        
        # Add each image to the database
        for i, image_data in enumerate(images, 1):
            filename = secure_filename(image_data['filename'])
            image = CarouselImage(
                filename=filename,
                title=image_data['title'],
                description=image_data['description'],
                order=i,
                is_active=True
            )
            
            # Check if image already exists
            existing = CarouselImage.query.filter_by(filename=filename).first()
            if existing:
                print(f"Image {filename} already exists in database")
                continue
                
            # Add to database
            CarouselImage.db.session.add(image)
            print(f"Added image {filename} to database")
        
        # Commit changes
        CarouselImage.db.session.commit()
        print(f"Added {len(images)} images to the carousel database")

if __name__ == '__main__':
    add_carousel_images() 