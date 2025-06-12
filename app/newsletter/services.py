from datetime import datetime, timedelta
from flask import current_app, render_template
from app.extensions import db, mail
from app.models import User, Location, UserPreferences
from app.newsletter.models import NewsletterSubscription
from app.bird_tracker import BirdSightingTracker
import logging
from flask_mail import Message

logger = logging.getLogger(__name__)

class NewsletterService:
    def __init__(self):
        self.tracker = BirdSightingTracker()
        
    def get_subscribed_users(self):
        """Get all users with active newsletter subscriptions."""
        try:
            users = User.query.join(NewsletterSubscription).filter(
                NewsletterSubscription.is_active == True
            ).all()
            logger.info(f"Found {len(users)} subscribed users")
            return users
        except Exception as e:
            logger.error(f"Error getting subscribed users: {str(e)}")
            return []
        
    def get_user_active_location(self, user):
        """Get the user's active location, or Cincinnati if not set."""
        user_pref = UserPreferences.query.filter_by(user_id=user.id).first()
        location = None
        if user_pref and user_pref.active_location_id:
            location = Location.query.get(user_pref.active_location_id)
        if not location:
            location = Location.query.filter_by(name="Cincinnati, OH").first()
        return location

    def get_user_observations(self, user, days=7):
        """Get recent observations for a user's active location."""
        try:
            location = self.get_user_active_location(user)
            if not location:
                logger.warning(f"User {user.email} has no active location set, using Cincinnati")
                location = Location.query.filter_by(name="Cincinnati, OH").first()
                if not location:
                    logger.error("Default Cincinnati location not found")
                    return []
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            observations = self.tracker.get_observations(
                location=location,
                start_date=start_date,
                end_date=end_date
            )
            logger.info(f"Retrieved {len(observations)} observations for user {user.email}")
            return observations
        except Exception as e:
            logger.error(f"Error getting observations for user {user.email}: {str(e)}")
            return []
        
    def generate_report(self, user, observations):
        """Generate personalized report content."""
        try:
            analysis = self.tracker.analyze_recent_sightings(observations, user_id=user.id)
            location = self.get_user_active_location(user)
            if not location:
                location = Location.query.filter_by(name="Cincinnati, OH").first()
            html_content = render_template(
                'email/newsletter.html',
                user=user,
                location=location,
                observations=observations,
                analysis=analysis,
                date=datetime.now().strftime('%B %d, %Y')
            )
            return {
                'user': user,
                'location': location,
                'observations': observations,
                'analysis': analysis,
                'html_content': html_content
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
                
            # Create email message
            msg = Message(
                subject=f"Weekly Bird Sighting Report - {datetime.now().strftime('%Y-%m-%d')}",
                recipients=[user.email],
                html=report_data['html_content']
            )
            
            # Send email
            mail.send(msg)
            
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
            logger.info(f"Starting weekly report generation for {len(users)} users")
            
            success_count = 0
            error_count = 0
            
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
                        error_count += 1
                        continue
                    
                    # Send report
                    if self.send_report(user, report_data):
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Error processing user {user.email}: {str(e)}")
                    error_count += 1
                    continue
            
            logger.info(f"Weekly report generation completed. Success: {success_count}, Errors: {error_count}")
            
        except Exception as e:
            logger.error(f"Error in weekly report generation: {str(e)}")
            raise 