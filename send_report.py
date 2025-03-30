from bird_tracker import BirdSightingTracker
import logging

def send_daily_report():
    try:
        # Initialize the tracker
        tracker = BirdSightingTracker()
        
        # Get recent observations
        observations = tracker.get_recent_observations()
        if not observations:
            logging.warning("No observations to report")
            return
            
        # Generate AI analysis
        analysis = tracker.analyze_observations()
        
        # Create static map
        map_image = tracker.create_static_map(observations)
        
        # Send email with report
        tracker.send_email(analysis, map_image)
        logging.info("Daily report sent successfully")
        
    except Exception as e:
        logging.error(f"Error sending daily report: {str(e)}")

if __name__ == "__main__":
    send_daily_report() 