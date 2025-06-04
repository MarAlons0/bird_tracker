from app import create_app
from app.newsletter.services import NewsletterService
import logging
import sys
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def is_monday():
    """Check if today is Monday in UTC."""
    utc_now = datetime.now(pytz.UTC)
    return utc_now.weekday() == 0  # 0 is Monday

def main():
    """Send weekly reports to all subscribed users if it's Monday."""
    if not is_monday():
        logger.info("Not Monday, skipping report generation")
        return

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
    main() 