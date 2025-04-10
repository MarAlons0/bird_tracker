from bird_tracker import BirdSightingTracker
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Initializing scheduler...")
        tracker = BirdSightingTracker()
        logger.info("Scheduler initialized successfully")
        
        # Keep the process running
        while True:
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"Error in scheduler: {str(e)}")
        raise

if __name__ == "__main__":
    main() 