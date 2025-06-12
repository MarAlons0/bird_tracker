import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.report_app import create_app
from app.models import User, db, Location, UserPreferences, BirdSightingCache
from app.newsletter.models import NewsletterSubscription
from datetime import datetime

# Set environment variables from Heroku
os.environ['DATABASE_URL'] = 'postgres://u393psopndshbh:p18ba7986cd5ad98b91e865897e2115a1efbdad521c3c82df5a93ef977c206452@cd5gks8n4kb20g.cluster-czrs8kj4isg7.us-east-1.rds.amazonaws.com:5432/dca2lkdkae52ej'
os.environ['MAIL_SERVER'] = 'smtp.gmail.com'
os.environ['MAIL_PORT'] = '587'
os.environ['MAIL_USE_TLS'] = 'true'
os.environ['MAIL_USERNAME'] = 'mariobirdtracker@gmail.com'
os.environ['MAIL_PASSWORD'] = 'ywezmdmgyyzcmesi'
os.environ['MAIL_DEFAULT_SENDER'] = 'mariobirdtracker@gmail.com'
os.environ['EBIRD_API_KEY'] = '7pgb8l664h94'

def test_newsletter():
    # Create and configure the app
    app = create_app()
    
    with app.app_context():
        # Delete existing SQLite database if it exists
        db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'bird_tracker.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            print("Deleted existing database")
        
        db.create_all()  # Create new database with updated schema
        try:
            # Clean up any existing bird sighting cache
            BirdSightingCache.query.delete()
            db.session.commit()
            print("Cleared bird sighting cache.")

            # Delete existing user if it exists
            existing_user = User.query.filter_by(email='mariobirdtracker@gmail.com').first()
            if existing_user:
                # First delete any cache records for this user
                BirdSightingCache.query.filter_by(user_id=existing_user.id).delete()
                db.session.commit()
                db.session.delete(existing_user)
                db.session.commit()
            
            # Create a test user
            test_user = User(
                email='mariobirdtracker@gmail.com'
            )
            db.session.add(test_user)
            db.session.commit()  # Commit to get a valid user ID
            
            # Create a default location
            default_location = Location(
                name='Cincinnati, OH',
                latitude=39.1031,
                longitude=-84.512,
                radius=25.0,
                is_active=True
            )
            db.session.add(default_location)
            db.session.commit()
            
            # Set as user's active location
            user_prefs = UserPreferences(
                user_id=test_user.id,
                active_location_id=default_location.id,
                default_location_id=default_location.id
            )
            db.session.add(user_prefs)
            db.session.commit()
            
            # Create newsletter subscription
            subscription = NewsletterSubscription(
                user_id=test_user.id,
                is_active=True
            )
            db.session.add(subscription)
            db.session.commit()
            
            print(f"Created test user: {test_user.email}")
            print(f"Created newsletter subscription for user {test_user.id}")
            
            # Verify the setup
            user = User.query.filter_by(email='mariobirdtracker@gmail.com').first()
            if user and user.newsletter_subscription:
                print("Newsletter setup verified successfully!")
                print(f"Newsletter active: {user.newsletter_subscription.is_active}")
                
                # Create BirdSightingTracker with db instance
                from app.bird_tracker import BirdSightingTracker
                tracker = BirdSightingTracker(db_instance=db, app=app)
                
                # Create NewsletterService with tracker
                from app.newsletter.services import NewsletterService
                service = NewsletterService()
                service.tracker = tracker
                
                # Get observations and generate report
                observations = tracker.get_recent_observations(user.id)
                if observations:
                    report = service.generate_report(user, observations)
                    if report:
                        print("\nGenerated report successfully!")
                        if service.send_report(user, report):
                            print("Report sent successfully!")
                        else:
                            print("Failed to send report.")
                    else:
                        print("Failed to generate report.")
                else:
                    print("No observations found.")
            else:
                print("Error: Newsletter setup verification failed")
                
        except Exception as e:
            print(f"Error during test: {str(e)}")
            db.session.rollback()
        finally:
            # Clean up test data
            if 'test_user' in locals():
                # First delete any cache records for this user
                BirdSightingCache.query.filter_by(user_id=test_user.id).delete()
                db.session.commit()
                # Then delete the user
                db.session.delete(test_user)
                db.session.commit()
                print("Cleaned up test data")

if __name__ == '__main__':
    test_newsletter() 