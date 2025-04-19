from datetime import datetime, timedelta
from flask import current_app, render_template
from app.extensions import db, mail
from app.models import User, Location
from app.newsletter.models import NewsletterSubscription
from app.bird_tracker import BirdSightingTracker

class NewsletterService:
    def __init__(self):
        self.tracker = BirdSightingTracker()
        
    def get_subscribed_users(self):
        """Get all users with active newsletter subscriptions."""
        return User.query.join(NewsletterSubscription).filter(
            NewsletterSubscription.is_active == True
        ).all()
        
    def get_user_observations(self, user, days=7):
        """Get recent observations for a user's default location."""
        if not user.default_location:
            current_app.logger.warning(f"User {user.email} has no default location set")
            return []
            
        try:
            observations = self.tracker.get_recent_observations(
                user_id=user.id,
                days_back=days
            )
            return observations
        except Exception as e:
            current_app.logger.error(f"Error getting observations for user {user.email}: {str(e)}")
            return []
        
    def generate_report(self, user, observations):
        """Generate personalized report content."""
        try:
            analysis = self.tracker.analyze_recent_sightings(observations, user_id=user.id)
            return {
                'user': user,
                'location': user.default_location,
                'observations': observations,
                'analysis': analysis
            }
        except Exception as e:
            current_app.logger.error(f"Error generating report for user {user.email}: {str(e)}")
            return None
        
    def send_report(self, user, report_data):
        """Send the newsletter report to a user."""
        try:
            if not report_data:
                current_app.logger.warning(f"No report data for user {user.email}")
                return False
                
            # Create email template
            template = self.tracker.create_email_template(
                analysis=report_data['analysis'],
                location_name=report_data['location'].name,
                observations=report_data['observations']
            )
            
            if not template:
                current_app.logger.error(f"Failed to create email template for {user.email}")
                return False
            
            # Send email
            self.tracker.send_email(
                subject=f"Weekly Bird Sighting Report - {datetime.now().strftime('%Y-%m-%d')}",
                body=template,
                recipient=user.email
            )
            
            # Update last sent timestamp
            subscription = user.newsletter_subscription
            subscription.last_sent = datetime.utcnow()
            db.session.commit()
            
            current_app.logger.info(f"Successfully sent report to {user.email}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error sending report to {user.email}: {str(e)}")
            return False 