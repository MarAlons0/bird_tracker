import os
from app.report_app import create_app
from app.models import User, NewsletterSubscription, db
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
        try:
            # Create a test user
            test_user = User(
                email='test@example.com',
                is_subscribed=True,
                default_location='Cincinnati'
            )
            db.session.add(test_user)
            db.session.flush()  # Get the user ID without committing
            
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
            user = User.query.filter_by(email='test@example.com').first()
            if user and user.newsletter_subscription:
                print("Newsletter setup verified successfully!")
                print(f"User subscribed: {user.is_subscribed}")
                print(f"Newsletter active: {user.newsletter_subscription.is_active}")
            else:
                print("Error: Newsletter setup verification failed")
                
        except Exception as e:
            print(f"Error during test: {str(e)}")
            db.session.rollback()
        finally:
            # Clean up test data
            if 'test_user' in locals():
                db.session.delete(test_user)
                db.session.commit()
                print("Cleaned up test data")

if __name__ == '__main__':
    test_newsletter() 