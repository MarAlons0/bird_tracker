from app import create_app
from app.extensions import db
from app.models import User, Location, BirdSighting, UserPreferences, RegistrationRequest, CarouselImage, BirdSightingCache
from app.newsletter.models import NewsletterSubscription
import os

app = create_app()
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"Current working directory: {os.getcwd()}")
print(f"Database file exists: {os.path.exists('bird_tracker.db')}")

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully!")
    
    # Verify tables were created
    print("\nVerifying tables...")
    for table in db.metadata.tables:
        print(f"Found table: {table}") 