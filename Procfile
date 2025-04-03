web: gunicorn "app:create_app()"
scheduler: python -c "from bird_tracker import BirdSightingTracker; tracker = BirdSightingTracker(); import time; time.sleep(1); tracker.scheduler.print_jobs()" 