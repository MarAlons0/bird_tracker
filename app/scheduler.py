from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from app import create_app
# Removed newsletter import since we removed that functionality
import logging
import os
import sys
import time
import pytz

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
        scheduler = BackgroundScheduler(timezone=pytz.UTC)
        
        # Add error handler
        scheduler.add_listener(handle_job_error, EVENT_JOB_ERROR | EVENT_JOB_MISSED)
        
        # Schedule weekly reports to run every Monday at 9:00 AM UTC
        # Note: This is a placeholder since we removed newsletter functionality
        scheduler.add_job(
            send_weekly_reports,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0, timezone=pytz.UTC),
            id='send_weekly_reports',
            name='Send weekly bird sighting reports',
            replace_existing=True,
            misfire_grace_time=3600  # Allow jobs to run up to 1 hour late
        )
        
        try:
            scheduler.start()
            logger.info("Started weekly report scheduler (runs every Monday at 9:00 AM UTC)")
            
            # Keep the scheduler running
            while True:
                time.sleep(60)  # Sleep for 1 minute
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error in scheduler: {str(e)}")
            if scheduler.running:
                scheduler.shutdown()
            sys.exit(1)
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
            # Placeholder for weekly reports - newsletter functionality was removed
            logger.info("Weekly report generation completed successfully (placeholder)")
        except Exception as e:
            logger.error(f"Error in weekly report generation: {str(e)}")
            raise

if __name__ == '__main__':
    init_scheduler() 