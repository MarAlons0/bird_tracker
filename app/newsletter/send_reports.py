import logging
from app import create_app
from app.newsletter.services import NewsletterService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def send_weekly_reports():
    """Send weekly reports to all subscribed users."""
    app = create_app()
    
    with app.app_context():
        try:
            service = NewsletterService()
            users = service.get_subscribed_users()
            logger.info(f"Found {len(users)} subscribed users")
            
            for user in users:
                try:
                    # Get observations for the past week
                    observations = service.get_user_observations(user)
                    if not observations:
                        logger.warning(f"No observations found for user {user.email}")
                        continue
                    
                    # Generate report
                    report_data = service.generate_report(user, observations)
                    if not report_data:
                        logger.error(f"Failed to generate report for {user.email}")
                        continue
                    
                    # Send report
                    if service.send_report(user, report_data):
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

if __name__ == "__main__":
    send_weekly_reports() 