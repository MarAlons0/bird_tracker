from datetime import datetime, timedelta
from app import create_app
from app.models import User
from app.bird_tracker import BirdSightingTracker
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_weekly_reports():
    """Send weekly bird sighting reports to all subscribed users."""
    app = create_app()
    
    try:
        with app.app_context():
            # Get all subscribed users
            users = User.query.filter_by(is_subscribed=True).all()
            logger.info(f"Found {len(users)} subscribed users")
            
            # Initialize tracker
            tracker = BirdSightingTracker(db_instance=app.extensions['sqlalchemy'].db, app=app)
            
            # Calculate date range for the past week
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=7)
            
            for user in users:
                try:
                    if not user.default_location:
                        logger.warning(f"User {user.id} has no default location set")
                        continue
                        
                    # Get observations for the past week
                    observations = tracker.get_observations(
                        location=user.default_location,
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    if not observations:
                        logger.info(f"No observations found for user {user.id}")
                        continue
                        
                    # Generate analysis
                    analysis = tracker.analyze_observations(observations)
                    
                    # Create email template
                    email_template = tracker.create_email_template(
                        user=user,
                        observations=observations,
                        analysis=analysis
                    )
                    
                    # Send email
                    tracker.send_email(
                        recipient=user.email,
                        subject="Weekly Bird Sighting Report",
                        html_content=email_template
                    )
                    
                    logger.info(f"Successfully sent report to user {user.id}")
                    
                except Exception as e:
                    logger.error(f"Error processing user {user.id}: {str(e)}")
                    continue
                    
    except Exception as e:
        logger.error(f"Error sending weekly report: {str(e)}")
        raise
    finally:
        # Cleanup
        if 'tracker' in locals():
            tracker.cleanup()

if __name__ == '__main__':
    send_weekly_reports() 