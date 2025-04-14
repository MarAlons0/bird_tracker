from bird_tracker import BirdSightingTracker
import logging
import configparser
import os
from dotenv import load_dotenv
from datetime import datetime
import requests
import base64
from io import BytesIO

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_email_template(analysis, location_name):
    """Create HTML email template with map and analysis."""
    try:
        # Get Google Maps API key from environment
        google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
        if not google_maps_key:
            logger.error("Google Maps API key not found in environment variables")
            return None

        # Get recent observations for the map
        tracker = BirdSightingTracker()
        observations = tracker.get_recent_observations()
        
        if not observations:
            logger.error("No observations found for map generation")
            return None

        # Get the first observation's coordinates for the map center
        center_lat = observations[0]['lat']
        center_lng = observations[0]['lng']

        # Create markers for the map (limit to 50 markers)
        markers = []
        for obs in observations[:50]:  # Limit to 50 markers
            # Categorize birds by type
            if 'water' in obs['comName'].lower() or 'shore' in obs['comName'].lower():
                color = 'blue'  # Water birds
            elif 'hawk' in obs['comName'].lower() or 'eagle' in obs['comName'].lower():
                color = 'red'   # Raptors
            elif 'sparrow' in obs['comName'].lower() or 'finch' in obs['comName'].lower():
                color = 'gray'  # Small birds
            else:
                color = 'green' # Other birds
            markers.append(f"markers=color:{color}%7C{obs['lat']},{obs['lng']}")

        # Create map URL
        map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lng}&zoom=10&size=800x400&maptype=roadmap&{'&'.join(markers)}&key={google_maps_key}"
        logger.info(f"Generated map URL: {map_url}")  # Log the URL without the API key

        # Create HTML template with map and legend
        template = f"""
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
                    padding: 40px 20px;
                    text-align: center;
                    color: white;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }}
                .title {{
                    font-size: 24px;
                    font-weight: bold;
                    margin: 0;
                }}
                .map-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .map {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }}
                .legend {{
                    display: flex;
                    justify-content: center;
                    flex-wrap: wrap;
                    gap: 15px;
                    margin: 15px 0;
                }}
                .legend-item {{
                    display: flex;
                    align-items: center;
                    gap: 5px;
                }}
                .legend-color {{
                    width: 15px;
                    height: 15px;
                    border-radius: 50%;
                }}
                .legend-text {{
                    font-size: 14px;
                }}
                .analysis {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-radius: 4px;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="banner">
                <h1 class="title">Weekly Bird Sighting Report</h1>
                <p>{location_name}</p>
            </div>
            
            <div class="map-container">
                <img src="{map_url}" alt="Bird Sightings Map" class="map">
                <div class="legend">
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #e74c3c;"></div>
                        <span class="legend-text">Raptors</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #3498db;"></div>
                        <span class="legend-text">Waterfowl</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #2ecc71;"></div>
                        <span class="legend-text">Songbirds</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background-color: #95a5a6;"></div>
                        <span class="legend-text">Other</span>
                    </div>
                </div>
            </div>
            
            <div class="analysis">
                {analysis}
            </div>
        </body>
        </html>
        """
        return template
    except Exception as e:
        logger.error(f"Error creating email template: {str(e)}")
        return None

def send_weekly_report():
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
        email_content = create_email_template(analysis, location_name)
        
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
        logger.info("Weekly report sent successfully")
        
    except Exception as e:
        logger.error(f"Error sending weekly report: {str(e)}")

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
    
    send_weekly_report() 