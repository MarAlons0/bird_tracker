from flask import current_app
from app.models import BirdSighting
from datetime import datetime, timedelta

def send_weekly_bird_sighting_report():
    """Send a weekly report of bird sightings."""
    try:
        # Get bird sightings from the last week
        week_ago = datetime.utcnow() - timedelta(days=7)
        sightings = BirdSighting.query.filter(BirdSighting.timestamp >= week_ago).all()
        
        # Log the report generation
        current_app.logger.info(f"Generating weekly report with {len(sightings)} sightings")
        
        # TODO: Implement email sending functionality
        
    except Exception as e:
        current_app.logger.error(f"Error sending weekly report: {str(e)}")
        raise 