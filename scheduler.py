from bird_tracker import BirdSightingTracker
import time
import logging
import signal
import sys
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global flag to control the main loop
running = True

def signal_handler(signum, frame):
    """Handle termination signals gracefully"""
    global running
    logger.info(f"Received signal {signum}. Shutting down gracefully...")
    running = False

def main():
    try:
        # Set up signal handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        logger.info("Initializing scheduler...")
        tracker = BirdSightingTracker()
        logger.info("Scheduler initialized successfully")
        
        # Keep the process running until signaled to stop
        while running:
            current_time = datetime.now()
            # Get schedule from tracker config
            hour = int(tracker.config['email_schedule']['hour'])
            minute = int(tracker.config['email_schedule']['minute'])
            day = int(tracker.config['email_schedule']['day'])
            
            # Check if it's time to run the report
            if current_time.weekday() == day and current_time.hour == hour and current_time.minute == minute:
                try:
                    logger.info("Running weekly report job...")
                    tracker.send_weekly_report()
                    logger.info("Weekly report job completed successfully")
                except Exception as e:
                    logger.error(f"Error running weekly report job: {str(e)}")
            
            # Sleep for 1 minute before next check
            time.sleep(60)
            
        logger.info("Scheduler shutting down...")
            
    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 