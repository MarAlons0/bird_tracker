from datetime import datetime, timedelta
from flask import current_app, render_template
from app.extensions import db, mail
from app.models import User, Location
from app.newsletter.models import NewsletterSubscription
from app.bird_tracker import BirdSightingTracker
import logging

logger = logging.getLogger(__name__)

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
        location = user.default_location
        if not location:
            logger.warning(f"User {user.email} has no default location set, using Cincinnati")
            # Use Cincinnati as default location
            location = Location.query.filter_by(name="Cincinnati").first()
            if not location:
                logger.error("Default Cincinnati location not found")
                return []
            
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            observations = self.tracker.get_observations(
                location=location,
                start_date=start_date,
                end_date=end_date
            )
            return observations
        except Exception as e:
            logger.error(f"Error getting observations for user {user.email}: {str(e)}")
            return []
        
    def generate_report(self, user, observations):
        """Generate personalized report content."""
        try:
            analysis = self.tracker.analyze_recent_sightings(observations, user_id=user.id)
            location = user.default_location or Location.query.filter_by(name="Cincinnati").first()
            
            return {
                'user': user,
                'location': location,
                'observations': observations,
                'analysis': analysis
            }
        except Exception as e:
            logger.error(f"Error generating report for user {user.email}: {str(e)}")
            return None
        
    def send_report(self, user, report_data):
        """Send the newsletter report to a user."""
        try:
            if not report_data:
                logger.warning(f"No report data for user {user.email}")
                return False
                
            # Create email template
            template = self.tracker.create_email_template(
                user=user,
                observations=report_data['observations'],
                analysis=report_data['analysis']
            )
            
            if not template:
                logger.error(f"Failed to create email template for {user.email}")
                return False
            
            # Send email
            self.tracker.send_email(
                to=[user.email],
                subject=f"Weekly Bird Sighting Report - {datetime.now().strftime('%Y-%m-%d')}",
                html=template
            )
            
            # Update last sent timestamp
            subscription = user.newsletter_subscription
            subscription.last_sent = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Successfully sent report to {user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending report to {user.email}: {str(e)}")
            return False
            
    def send_weekly_reports(self):
        """Send weekly reports to all subscribed users."""
        try:
            users = self.get_subscribed_users()
            logger.info(f"Found {len(users)} subscribed users")
            
            for user in users:
                try:
                    # Get observations for the past week
                    observations = self.get_user_observations(user)
                    if not observations:
                        logger.warning(f"No observations found for user {user.email}")
                        continue
                    
                    # Generate report
                    report_data = self.generate_report(user, observations)
                    if not report_data:
                        logger.error(f"Failed to generate report for {user.email}")
                        continue
                    
                    # Send report
                    if self.send_report(user, report_data):
                        logger.info(f"Successfully sent report to {user.email}")
                    else:
                        logger.error(f"Failed to send report to {user.email}")
                        
                except Exception as e:
                    logger.error(f"Error processing user {user.email}: {str(e)}")
                    continue
            
            logger.info("Weekly report generation completed")
            
        except Exception as e:
            logger.error(f"Error in weekly report generation: {str(e)}")
            raise 