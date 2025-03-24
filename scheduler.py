# New file for handling scheduled tasks
import os
from bird_tracker import BirdSightingTracker
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler

load_dotenv()

def send_daily_report():
    tracker = BirdSightingTracker()
    tracker.generate_daily_report()

scheduler = BlockingScheduler()
scheduler.add_job(send_daily_report, 'cron', hour=8, minute=0)
scheduler.start()

if __name__ == "__main__":
    tracker = BirdSightingTracker()
    # The scheduler will keep running
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        tracker.scheduler.shutdown() 