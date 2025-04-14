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

def create_email_template(analysis, location_name, observations):
    """Create a nicely formatted email template with banner and proper styling"""
    current_date = datetime.now().strftime("%B %d, %Y")
    
    # Create map HTML
    map_html = ""
    if observations:
        try:
            # Get Google Places API key from environment (includes Maps API access)
            google_maps_key = os.getenv('GOOGLE_PLACES_API_KEY')
            if not google_maps_key:
                logger.error("Google Places API key not found in environment variables")
                raise ValueError("Google Places API key not found")
            
            # Create a map centered on the first observation
            center_lat = float(observations[0]['lat'])
            center_lng = float(observations[0]['lng'])
            
            # Bird categorization function
            def categorize_bird(bird_name):
                raptors = ['hawk', 'eagle', 'falcon', 'owl', 'osprey', 'kite', 'harrier', 'vulture']
                waterfowl = ['duck', 'goose', 'swan', 'heron', 'egret', 'crane', 'grebe', 'loon', 'coot', 'gallinule', 'rail', 'shorebird', 'sandpiper', 'plover', 'gull', 'tern']
                songbirds = ['warbler', 'sparrow', 'finch', 'thrush', 'wren', 'chickadee', 'titmouse', 'nuthatch', 'creeper', 'kinglet', 'gnatcatcher', 'flycatcher', 'phoebe', 'pewee', 'vireo', 'jay', 'crow', 'raven', 'blackbird', 'oriole', 'grackle', 'starling', 'mockingbird', 'thrasher', 'catbird', 'cardinal', 'grosbeak', 'bunting', 'towhee', 'junco', 'lark', 'pipit', 'swallow', 'martin', 'swift', 'hummingbird', 'woodpecker', 'flicker', 'sapsucker']
                
                bird_name_lower = bird_name.lower()
                
                if any(term in bird_name_lower for term in raptors):
                    return 'raptor'
                elif any(term in bird_name_lower for term in waterfowl):
                    return 'waterfowl'
                elif any(term in bird_name_lower for term in songbirds):
                    return 'songbird'
                else:
                    return 'other'
            
            # Limit the number of markers to 20 to keep the URL length manageable
            max_markers = 20
            markers = []
            for obs in observations[:max_markers]:
                lat = float(obs['lat'])
                lng = float(obs['lng'])
                category = categorize_bird(obs['comName'])
                color = {
                    'raptor': 'red',
                    'waterfowl': 'blue',
                    'songbird': 'green',
                    'other': 'gray'
                }[category]
                markers.append(f"markers=color:{color}%7C{lat},{lng}")
            
            # Create static map URL with proper encoding
            map_url = f"https://maps.googleapis.com/maps/api/staticmap?center={center_lat},{center_lng}&zoom=10&size=800x400&maptype=roadmap&{'&'.join(markers)}&key={google_maps_key}"
            
            # Log the map URL for debugging (without the API key)
            logger.info(f"Generated map URL: {map_url.split('&key=')[0]}")
            
            try:
                # Download the map image and convert to base64
                response = requests.get(map_url)
                if response.status_code == 200:
                    # Convert image to base64
                    image_data = base64.b64encode(response.content).decode('utf-8')
                    map_src = f"data:image/png;base64,{image_data}"
                else:
                    logger.error(f"Failed to download map image: {response.status_code}")
                    raise Exception("Failed to download map image")
            except Exception as e:
                logger.error(f"Error processing map image: {str(e)}")
                # Use fallback image from our server
                fallback_url = "https://bird-tracker-dev-a7bb94e09a81.herokuapp.com/static/images/map-placeholder.png"
                response = requests.get(fallback_url)
                if response.status_code == 200:
                    image_data = base64.b64encode(response.content).decode('utf-8')
                    map_src = f"data:image/png;base64,{image_data}"
                else:
                    map_src = fallback_url
            
            # Create HTML template with base64-encoded image and legend
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
                        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
                    }}
                    .title {{
                        font-size: 24px;
                        margin: 0;
                        font-weight: bold;
                    }}
                    .subtitle {{
                        font-size: 18px;
                        margin: 10px 0 0;
                    }}
                    .content {{
                        background-color: #f9f9f9;
                        padding: 20px;
                        border-radius: 5px;
                        margin-bottom: 20px;
                    }}
                    .map-container {{
                        margin: 20px 0;
                        text-align: center;
                        position: relative;
                    }}
                    .map-image {{
                        max-width: 100%;
                        height: auto;
                        border: 1px solid #ddd;
                        border-radius: 5px;
                    }}
                    .legend {{
                        position: absolute;
                        bottom: 10px;
                        right: 10px;
                        background: white;
                        padding: 10px;
                        border-radius: 5px;
                        box-shadow: 0 0 15px rgba(0,0,0,0.2);
                        font-size: 12px;
                    }}
                    .legend-item {{
                        display: flex;
                        align-items: center;
                        margin-bottom: 5px;
                    }}
                    .legend-color {{
                        width: 15px;
                        height: 15px;
                        margin-right: 8px;
                        border-radius: 3px;
                    }}
                    .raptor {{ background-color: #e74c3c; }}
                    .waterfowl {{ background-color: #3498db; }}
                    .songbird {{ background-color: #2ecc71; }}
                    .other {{ background-color: #95a5a6; }}
                    .footer {{
                        text-align: center;
                        font-size: 12px;
                        color: #666;
                        margin-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="banner">
                    <h1 class="title">Weekly Bird Sighting Report</h1>
                    <p class="subtitle">{location_name}</p>
                </div>
                <div class="content">
                    <div class="map-container">
                        <img src="{map_src}" 
                             alt="Bird Sighting Map" 
                             class="map-image"
                             style="display: block; margin: 0 auto;"
                             width="800"
                             height="400">
                        <div class="legend">
                            <div class="legend-item">
                                <div class="legend-color raptor"></div>
                                <span>Raptors</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color waterfowl"></div>
                                <span>Waterfowl</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color songbird"></div>
                                <span>Songbirds</span>
                            </div>
                            <div class="legend-item">
                                <div class="legend-color other"></div>
                                <span>Other Birds</span>
                            </div>
                        </div>
                    </div>
                    {analysis}
                </div>
                <div class="footer">
                    <p>This is an automated report from Bird Tracker. To manage your preferences, visit the Bird Tracker website.</p>
                </div>
            </body>
            </html>
            """
        except Exception as e:
            logger.error(f"Error creating map: {str(e)}")
            # Add a fallback image if map generation fails
            map_html = f"""
            <div class="map-container" style="margin: 20px 0; text-align: center;">
                <img 
                    src="https://bird-tracker-dev-a7bb94e09a81.herokuapp.com/static/images/map-placeholder.png" 
                    alt="Map placeholder"
                    style="max-width: 100%; height: auto; border-radius: 5px;"
                />
                <div style="margin-top: 10px; font-size: 12px; color: #666;">
                    Map showing recent bird sightings in {location_name} ({len(observations)} sightings)
                </div>
            </div>
            """
    
    return html_content

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