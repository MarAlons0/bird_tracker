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

        # Create legend HTML
        legend_html = """
        <div style="margin: 20px 0; padding: 10px; background: #f8f9fa; border-radius: 5px;">
            <h3 style="margin: 0 0 10px 0; color: #333;">Map Legend</h3>
            <div style="display: flex; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; margin-right: 15px;">
                    <div style="width: 20px; height: 20px; background: blue; margin-right: 5px;"></div>
                    <span>Water Birds</span>
                </div>
                <div style="display: flex; align-items: center; margin-right: 15px;">
                    <div style="width: 20px; height: 20px; background: red; margin-right: 5px;"></div>
                    <span>Raptors</span>
                </div>
                <div style="display: flex; align-items: center; margin-right: 15px;">
                    <div style="width: 20px; height: 20px; background: gray; margin-right: 5px;"></div>
                    <span>Small Birds</span>
                </div>
                <div style="display: flex; align-items: center;">
                    <div style="width: 20px; height: 20px; background: green; margin-right: 5px;"></div>
                    <span>Other Birds</span>
                </div>
            </div>
        </div>
        """

        # Create map HTML
        map_html = f"""
        <div class="map-container" style="margin: 20px 0; text-align: center;">
            <img 
                src="{map_url}" 
                alt="Bird Sighting Map"
                style="max-width: 100%; height: auto; border-radius: 5px;"
            />
            {legend_html}
        </div>
        """

        # Create HTML template with map and analysis
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Weekly Bird Sighting Report</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    margin: 0;
                    padding: 0;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #ffffff;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .banner {{
                    background-image: url('https://bird-tracker-app-9af5a4fb26d3.herokuapp.com/static/images/Banner.jpeg');
                    background-size: cover;
                    background-position: right center;
                    background-repeat: no-repeat;
                    height: 200px;
                    padding: 40px 20px;
                    text-align: left;
                    color: white;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    position: relative;
                    overflow: hidden;
                }}
                .banner::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: linear-gradient(to right, rgba(0,0,0,0.7) 0%, rgba(0,0,0,0.3) 100%);
                    z-index: 1;
                }}
                .banner-content {{
                    position: relative;
                    z-index: 2;
                    max-width: 60%;
                }}
                .title {{
                    font-size: 28px;
                    font-weight: bold;
                    margin: 0 0 10px 0;
                }}
                .subtitle {{
                    font-size: 16px;
                    margin: 0;
                }}
                .content {{
                    padding: 20px;
                }}
                .map-container {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .map-image {{
                    max-width: 100%;
                    height: auto;
                    border-radius: 5px;
                }}
                .analysis {{
                    margin-top: 20px;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 5px;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    font-size: 12px;
                    color: #666;
                    border-top: 1px solid #eee;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="banner">
                    <div class="banner-content">
                        <h1 class="title">Weekly Bird Sighting Report</h1>
                        <p class="subtitle">{location_name}</p>
                    </div>
                </div>
                <div class="content">
                    <div class="map-container">
                        <img src="{map_url}" 
                             alt="Bird Sighting Map" 
                             class="map-image"
                             style="display: block; margin: 0 auto;"
                             width="800"
                             height="400">
                        {legend_html}
                    </div>
                    <div class="analysis">
                        {analysis}
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated report generated by the Bird Tracker application.</p>
                    <p>To unsubscribe or manage your preferences, please visit the application settings.</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html_content
    except Exception as e:
        logger.error(f"Error creating map: {str(e)}")
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