from bird_tracker import BirdSightingTracker
import logging
import configparser
import os
from dotenv import load_dotenv
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_email_template(analysis, location_name, observations):
    """Create a nicely formatted email template with banner and proper styling"""
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Create map HTML
    map_html = ""
    if observations:
        try:
            # Create a map centered on the first observation
            center_lat = float(observations[0]['lat'])
            center_lng = float(observations[0]['lng'])
            
            # Create markers for all observations
            markers = []
            for obs in observations:
                lat = float(obs['lat'])
                lng = float(obs['lng'])
                markers.append(f"markers=color:red%7C{lat},{lng}")
            
            # Create static map URL
            map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lng}&zoom=10&size=800x400&maptype=roadmap&{'&'.join(markers)}&key=AIzaSyD8QJ5Qq7Qq7Qq7Qq7Qq7Qq7Qq7Qq7Qq7Q"
            
            map_html = f"""
            <div class="map-container" style="margin: 20px 0; text-align: center;">
                <img 
                    src="{map_url}" 
                    alt="Map of bird sightings in {location_name}"
                    style="max-width: 100%; height: auto; border-radius: 5px;"
                />
                <div style="margin-top: 10px; font-size: 12px; color: #666;">
                    Map showing recent bird sightings in {location_name}
                </div>
            </div>
            """
        except Exception as e:
            logger.error(f"Error creating map: {str(e)}")
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }}
        .banner {{
            background-image: url('https://bird-tracker-dev-a7bb94e09a81.herokuapp.com/static/images/Banner.jpeg');
            background-size: cover;
            background-position: center;
            color: white;
            text-align: center;
            padding: 40px 20px;
            margin-bottom: 20px;
            border-radius: 5px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
        }}
        .title {{
            font-size: 24px;
            margin-bottom: 10px;
            font-weight: bold;
        }}
        .subtitle {{
            font-size: 18px;
            margin-bottom: 20px;
        }}
        .content {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            margin-top: 20px;
        }}
        .map-container {{
            margin: 20px 0;
            border-radius: 5px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        ul {{
            margin-left: 20px;
        }}
        li {{
            margin-bottom: 8px;
        }}
    </style>
</head>
<body>
    <div class="banner">
        <div class="title">Mario's Bird Tracker Newsletter</div>
        <div class="subtitle">{current_date}</div>
    </div>
    
    <div class="content">
        <h2>Bird Sightings Report for {location_name}</h2>
        {map_html}
        {analysis}
    </div>
    
    <div style="margin-top: 20px; text-align: center; color: #666; font-size: 12px;">
        This report was generated automatically by the Bird Tracker application.
    </div>
</body>
</html>
"""

def send_daily_report():
    try:
        # Load environment variables
        load_dotenv()
        
        # Initialize the tracker
        tracker = BirdSightingTracker()
        
        # Get recent observations
        observations = tracker.get_recent_observations()
        if not observations:
            logger.warning("No observations to report")
            return
            
        # Generate AI analysis
        analysis = tracker.analyze_recent_sightings(observations)
        
        # Get location name
        location = tracker.get_active_location()
        location_name = location['name'] if location else "Cincinnati Area"
        
        # Create email content
        email_content = create_email_template(analysis, location_name, observations)
        
        # Get recipient email from environment variable
        recipient_email = os.getenv('RECIPIENT_EMAIL')
        if not recipient_email:
            logger.error("No recipient email configured")
            return
        
        # Send email with report
        tracker.send_email(
            subject=f"Mario's Bird Tracker Newsletter - {datetime.now().strftime('%B %d, %Y')}",
            body=email_content,
            recipient=recipient_email
        )
        logger.info("Daily report sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending daily report: {str(e)}")

if __name__ == "__main__":
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    # Verify email configuration
    if not config.has_section('email'):
        logging.error("Missing email configuration section")
        exit(1)
        
    required_email_settings = ['mail_server', 'mail_port', 'mail_username', 'mail_password']
    missing_settings = [setting for setting in required_email_settings 
                       if not config.has_option('email', setting)]
    
    if missing_settings:
        logging.error(f"Missing required email settings: {', '.join(missing_settings)}")
        exit(1)
    
    send_daily_report() 