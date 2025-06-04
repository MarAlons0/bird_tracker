from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from app import create_app
from app.newsletter.services import NewsletterService
import logging
import os
import sys
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def is_production():
    """Check if we're running in a production environment."""
    # Check for Heroku environment variables
    if os.environ.get('HEROKU_APP_NAME') or os.environ.get('DYNO'):
        return True
    # Check for other production indicators
    return os.environ.get('FLASK_ENV') == 'production' or os.environ.get('ENVIRONMENT') == 'production'

def init_scheduler():
    """Initialize the scheduler if in production environment."""
    if is_production():
        logger.info("Initializing scheduler in production environment...")
        scheduler = BackgroundScheduler()
        
        # Schedule weekly reports to run every Monday at 9:00 AM
        scheduler.add_job(
            send_weekly_reports,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='send_weekly_reports',
            name='Send weekly bird sighting reports',
            replace_existing=True,
            misfire_grace_time=3600  # Allow jobs to run up to 1 hour late
        )
        
        scheduler.start()
        logger.info("Started weekly report scheduler (runs every Monday at 9:00 AM)")
        
        # Keep the scheduler running
        try:
            while True:
                time.sleep(60)  # Sleep for 1 minute
        except (KeyboardInterrupt, SystemExit):
            scheduler.shutdown()
            logger.info("Scheduler shutdown")
    else:
        logger.info("Skipping scheduler setup in non-production environment")

def handle_job_error(event):
    """Handle scheduler job errors."""
    if event.exception:
        logger.error(f"Job {event.job_id} failed with error: {str(event.exception)}")
    else:
        logger.error(f"Job {event.job_id} was missed")

def send_weekly_reports():
    """Send weekly reports to all subscribed users."""
    logger.info("Starting weekly report generation...")
    app = create_app()
    
    with app.app_context():
        try:
            service = NewsletterService()
            service.send_weekly_reports()
            logger.info("Weekly report generation completed successfully")
        except Exception as e:
            logger.error(f"Error in weekly report generation: {str(e)}")
            raise

if __name__ == '__main__':
    init_scheduler() 