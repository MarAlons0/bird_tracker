from app import create_app, db
from app.models import CarouselImage

app = create_app()
app.app_context().push()

print('Number of carousel images:', CarouselImage.query.count())
print('Carousel images:', [{'id': img.id, 'title': img.title} for img in CarouselImage.query.all()]) 