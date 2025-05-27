from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from app import create_app
from app.newsletter.services import NewsletterService
import logging
import os

logger = logging.getLogger(__name__)

def init_scheduler():
    """Initialize the scheduler for weekly reports."""
    try:
        # Check if we're in production environment
        is_production = (
            os.getenv('FLASK_ENV') == 'production' or
            os.getenv('HEROKU_APP_NAME') in ['bird-tracker-app', 'bird-tracker-dev']
        )
        
        if not is_production:
            logger.info("Skipping scheduler setup in non-production environment")
            return

        scheduler = BackgroundScheduler()
        
        # Schedule weekly report email (every Monday at 9:00 AM)
        scheduler.add_job(
            func=send_weekly_reports,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_report',
            replace_existing=True
        )
        
        # Add error listener
        scheduler.add_listener(
            handle_job_error,
            EVENT_JOB_ERROR | EVENT_JOB_MISSED
        )
        
        scheduler.start()
        logger.info("Started weekly report scheduler (runs every Monday at 9:00 AM)")
        
    except Exception as e:
        logger.error(f"Error starting weekly reports: {str(e)}")
        raise

def handle_job_error(event):
    """Handle scheduler job errors."""
    if event.exception:
        logger.error(f"Job {event.job_id} failed: {str(event.exception)}")
    else:
        logger.error(f"Job {event.job_id} was missed")

def send_weekly_reports():
    """Send weekly reports to all subscribed users."""
    app = create_app()
    
    with app.app_context():
        try:
            service = NewsletterService()
            service.send_weekly_reports()
        except Exception as e:
            logger.error(f"Error in weekly report generation: {str(e)}")
            raise 