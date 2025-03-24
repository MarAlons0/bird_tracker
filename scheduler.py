# New file for handling scheduled tasks
import os
from bird_tracker import BirdSightingTracker
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    tracker = BirdSightingTracker()
    # The scheduler will keep running
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        tracker.scheduler.shutdown() 