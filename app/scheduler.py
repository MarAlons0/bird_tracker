from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging

logger = logging.getLogger(__name__)

# Initialize scheduler
scheduler = BackgroundScheduler()

def init_scheduler():
    """Initialize and start the scheduler."""
    try:
        # Import here to avoid circular imports
        from app.send_report import send_weekly_reports
        
        # Add job to send weekly reports every Monday at 9:00 AM
        scheduler.add_job(
            send_weekly_reports,
            trigger=CronTrigger(day_of_week='mon', hour=9, minute=0),
            id='weekly_report',
            name='Send weekly bird sighting reports',
            replace_existing=True
        )
        
        # Start the scheduler
        scheduler.start()
        logger.info("Scheduler initialized and started successfully")
        
    except Exception as e:
        logger.error(f"Error initializing scheduler: {str(e)}")
        raise 