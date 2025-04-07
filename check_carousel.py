from app import create_app
from models import CarouselImage

def check_carousel_images():
    app = create_app()
    with app.app_context():
        images = CarouselImage.query.limit(5).all()
        for img in images:
            print(f"Filename: {img.filename}")
            print(f"Cloudinary URL: {img.cloudinary_url}")
            print("-" * 50)

if __name__ == "__main__":
    check_carousel_images() 