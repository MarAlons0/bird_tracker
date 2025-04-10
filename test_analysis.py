from bird_tracker import BirdSightingTracker
from app import app

with app.app_context():
    tracker = BirdSightingTracker()
    print(tracker.analyze_sightings(1)) 