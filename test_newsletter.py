from app import create_app
from app.newsletter.services import NewsletterService
from app.models import User, BirdSighting, Location
from app.newsletter.models import NewsletterSubscription
from app.extensions import db
from datetime import datetime, timedelta
import pytz

def create_test_data():
    """Create test data for the newsletter."""
    # Remove any existing test user with this email
    existing_user = User.query.filter_by(email='alonsoencinci@gmail.com').first()
    if existing_user:
        # Delete any existing newsletter subscription
        existing_sub = NewsletterSubscription.query.filter_by(user_id=existing_user.id).first()
        if existing_sub:
            db.session.delete(existing_sub)
        db.session.delete(existing_user)
        db.session.commit()

    # Create a test user
    user = User(
        email='alonsoencinci@gmail.com',
        username='testuser',
        newsletter_subscription=True
    )
    db.session.add(user)
    db.session.commit()  # Commit the user first to get a valid ID
    
    # Create newsletter subscription
    subscription = NewsletterSubscription(
        user_id=user.id,
        is_active=True,
        created_at=datetime.utcnow()
    )
    db.session.add(subscription)
    db.session.commit()
    
    # Create a test location
    location = Location(
        name='Test Garden',
        latitude=40.7128,
        longitude=-74.0060,
        radius=1.0,
        is_active=True,
        user=user
    )
    db.session.add(location)
    db.session.commit()  # Commit the location
    
    # Create observations from the past week
    utc_now = datetime.now(pytz.UTC)
    sightings = []
    birds = [
        'American Robin',
        'Northern Cardinal',
        'Blue Jay'
    ]
    for i, bird_name in enumerate(birds):
        # Create 2-3 observations per bird
        for j in range(2 + (i % 2)):
            date = utc_now - timedelta(days=j)
            sighting = BirdSighting(
                bird_name=bird_name,
                location=location.name,
                latitude=location.latitude,
                longitude=location.longitude,
                timestamp=date,
                observer=user.username,
                notes=f'Saw {bird_name} in the garden'
            )
            db.session.add(sighting)
            sightings.append(sighting)
    db.session.commit()
    return user, sightings

def main():
    """Generate and send a test newsletter."""
    app = create_app()
    
    with app.app_context():
        db.create_all()  # Ensure all tables exist
        # Create test data
        user, sightings = create_test_data()
        
        # Generate report
        service = NewsletterService()
        report = service.generate_report(user, sightings)
        
        # Print the report
        print("\n=== Test Newsletter ===\n")
        print(report)
        
        # Optionally send the report
        if input("\nWould you like to send this test newsletter? (y/n): ").lower() == 'y':
            service.send_report(user, report)
            print("Test newsletter sent!")

if __name__ == '__main__':
    main() 