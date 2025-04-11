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
            # Check if it's Wednesday at 10:00 AM ET
            if current_time.weekday() == 2 and current_time.hour == 10 and current_time.minute == 0:  # 2 is Wednesday
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