from datetime import datetime, timedelta
from app.models import User, db
from app.bird_tracker import BirdSightingTracker
import logging

logger = logging.getLogger(__name__)

def send_weekly_reports():
    """Send weekly bird sighting reports to all subscribed users."""
    app = None
    try:
        # Create and configure the app
        from app.report_app import create_app
        app = create_app()
        
        # Get all subscribed users
        users = User.query.filter_by(is_subscribed=True).all()
        logger.info(f"Found {len(users)} subscribed users")
        
        # Initialize tracker
        tracker = BirdSightingTracker(db_instance=db, app=app)
        
        # Calculate date range for the past week
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        # Process each user
        for user in users:
            try:
                # Get user's default location
                location = user.default_location
                if not location:
                    logger.warning(f"User {user.email} has no default location set")
                    continue
                
                # Get observations for the past week
                observations = tracker.get_observations(
                    location=location,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not observations:
                    logger.info(f"No observations found for user {user.email}")
                    continue
                
                # Generate analysis
                analysis = tracker.generate_analysis(observations)
                
                # Create email template
                email_template = tracker.create_email_template(
                    user=user,
                    observations=observations,
                    analysis=analysis
                )
                
                # Send email
                tracker.send_email(
                    to=[user.email],
                    subject="Weekly Bird Sighting Report",
                    html=email_template
                )
                
                logger.info(f"Successfully sent report to {user.email}")
                
            except Exception as e:
                logger.error(f"Error processing user {user.email}: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error sending weekly report: {str(e)}")
        raise
    finally:
        # Clean up
        if app:
            app.app_context.pop() 