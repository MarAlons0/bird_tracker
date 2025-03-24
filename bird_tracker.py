import requests
from datetime import datetime, timedelta
from configparser import ConfigParser
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import anthropic
import os
import folium
import base64
from staticmap import StaticMap, CircleMarker
import io
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_MISSED
from dotenv import load_dotenv
import httpx
from anthropic import Anthropic

class BirdSightingTracker:
    def __init__(self):
        load_dotenv()
        self.config = self._load_config()
        self.api_key = os.getenv('EBIRD_API_KEY')
        self.base_url = "https://api.ebird.org/v2"
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': os.getenv('SMTP_USER'),
            'sender_password': os.getenv('SMTP_PASSWORD'),
            'admin_email': os.getenv('ADMIN_EMAIL'),
            'recipient': os.getenv('RECIPIENT_EMAIL')
        }
        self.active_location = self._get_active_location()
        
        # Update this part
        http_client = httpx.Client()
        self.claude = Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY'),
            http_client=http_client
        )
        
        # Start daily report scheduler
        self.scheduler = self.start_daily_reports()
    
    def _load_config(self):
        config = ConfigParser()
        config_path = 'config.ini'  # Changed to relative path
        print(f"DEBUG: Loading config from: {config_path}")
        if config.read(config_path):
            print("DEBUG: Config file loaded successfully")
            print(f"DEBUG: Sections found: {config.sections()}")
            return config
        else:
            # Fall back to environment variables if config file not found
            print("DEBUG: Config file not found, using environment variables")
            config.add_section('locations')
            config.add_section('email_schedule')
            config['locations']['active_location'] = 'cincinnati'
            config['email_schedule']['hour'] = '7'
            config['email_schedule']['minute'] = '0'
            return config
    
    def _get_active_location(self):
        """Get location from environment or use default"""
        return {
            'name': os.getenv('DEFAULT_LOCATION_NAME', 'Cincinnati'),
            'latitude': float(os.getenv('DEFAULT_LATITUDE', '39.1031')),
            'longitude': float(os.getenv('DEFAULT_LONGITUDE', '-84.5120')),
            'radius': float(os.getenv('DEFAULT_RADIUS', '25'))
        }
    
    def get_taxonomic_info(self, species_code):
        """
        Get taxonomic information for a species
        """
        try:
            # For now, just return basic info from the observation
            return {
                'family': 'Unknown Family',  # We'll add proper taxonomy later
                'genus': 'Unknown Genus',
                'species': species_code
            }
        except Exception as e:
            print(f"DEBUG: Error getting taxonomy: {str(e)}")
            return None
    
    def get_recent_observations(self, species_list=None):
        """
        Get recent bird sightings within radius of active location
        """
        endpoint = f"{self.base_url}/data/obs/geo/recent"
        headers = {'X-eBirdApiToken': self.api_key}
        params = {
            'lat': float(self.active_location['latitude']),
            'lng': float(self.active_location['longitude']),
            'dist': float(self.active_location['radius']),
            'back': 21,
            'maxResults': 1000
        }
        
        print(f"DEBUG: Making API request...")
        response = requests.get(endpoint, headers=headers, params=params)
        print(f"DEBUG: API Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                observations = response.json()
                print(f"DEBUG: Successfully parsed {len(observations)} observations")
                
                # Add taxonomic information to each observation
                for obs in observations:
                    print(f"DEBUG: Processing observation for {obs.get('comName', 'Unknown')}")
                    taxa = self.get_taxonomic_info(obs['speciesCode'])
                    if taxa:
                        obs.update(taxa)
                
                return observations
            except Exception as e:
                print(f"DEBUG: Error parsing response: {str(e)}")
                return None
        else:
            print(f"DEBUG: API Error Response: {response.text}")
            return None
    
    def analyze_observations(self, observations):
        """Generate insights using Claude about the bird observations"""
        if not observations:
            return "No observations to analyze."

        try:
            # Prepare data for Claude with week-by-week comparison
            current_week = []
            previous_week = []
            species_count_current = {}
            species_count_previous = {}
            locations = set()
            birds_of_prey = set()
            
            # Split observations into current and previous week
            one_week_ago = datetime.now() - timedelta(days=7)
            
            for obs in observations:
                species = obs['comName']
                count = obs.get('howMany', 1)
                location = obs['locName']
                date = datetime.strptime(obs['obsDt'].split()[0], '%Y-%m-%d')
                
                if date >= one_week_ago:
                    current_week.append(f"{species} ({count} seen at {location} on {obs['obsDt']})")
                    species_count_current[species] = species_count_current.get(species, 0) + count
                else:
                    previous_week.append(f"{species} ({count} seen at {location} on {obs['obsDt']})")
                    species_count_previous[species] = species_count_previous.get(species, 0) + count
                
                locations.add(location)
                
                if any(term in species.lower() for term in ['hawk', 'eagle', 'owl', 'falcon', 'kite', 'osprey']):
                    birds_of_prey.add(species)

            print("DEBUG: Data prepared successfully")
            print(f"DEBUG: Current week species: {len(species_count_current)}")
            print(f"DEBUG: Previous week species: {len(species_count_previous)}")
            print(f"DEBUG: Birds of prey found: {len(birds_of_prey)}")

            # Create the prompt
            prompt = f"""Analyze these Cincinnati bird observations with week-over-week comparison:

Two-Week Summary:
Current Week Species: {len(species_count_current)}
Previous Week Species: {len(species_count_previous)}
Birds of Prey: {', '.join(birds_of_prey)}
Total Locations: {len(locations)}

Current Week Highlights:
{chr(10).join(current_week[:10])}  # Show first 10 observations

Previous Week Highlights:
{chr(10).join(previous_week[:10])}  # Show first 10 observations

Please provide a brief analysis focusing on:
1. Notable changes between weeks
2. Significant bird of prey activity
3. Key locations for observation
4. Migration patterns

5. Rare Bird Alerts
   - Unusual species for the region
   - Species outside their normal range
   - First-of-season sightings

6. Photography Tips
   - Best times for specific species
   - Recommended locations and setups
   - Target species behavior patterns
"""

            print("DEBUG: Sending request to Claude...")
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            print("DEBUG: Claude response received")
            return response.content[0].text

        except Exception as e:
            print(f"DEBUG: Error in analyze_observations: {str(e)}")
            return "Error generating insights. Using basic summary instead."

    def create_static_map(self, observations):
        """Create a static map of bird observations"""
        print("DEBUG: Starting static map creation...")
        try:
            # Add User-Agent header and use CartoDB tiles
            headers = {
                'User-Agent': 'BirdTracker/1.0 (https://bird-tracker-app-9af5a4fb26d3.herokuapp.com/)'
            }
            m = StaticMap(800, 600, 
                         url_template='https://cartodb-basemaps-a.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
                         headers=headers)

            # Process observations
            for obs in observations:
                try:
                    # Try to get coordinates from the location name
                    coords = None
                    if 'US-OH' in obs['locName']:
                        loc_parts = obs['locName'].split('US-OH')
                        if len(loc_parts) > 1:
                            try:
                                coords_text = loc_parts[1].strip()
                                lat, lng = map(float, coords_text.split(','))
                                coords = (lng, lat)  # Note: StaticMap uses (lng, lat) order
                            except:
                                coords = None

                    # If no coordinates found, use Cincinnati coordinates
                    if not coords:
                        coords = (-84.5120, 39.1031)  # Cincinnati coordinates

                    # Determine marker color based on bird type
                    species = obs['comName']
                    if any(term in species.lower() for term in ['hawk', 'eagle', 'owl', 'falcon', 'kite', 'osprey']):
                        color = '#ff0000'  # Red for raptors
                    elif any(term in species.lower() for term in ['duck', 'goose', 'swan', 'merganser', 'teal']):
                        color = '#0000ff'  # Blue for waterfowl
                    elif any(term in species.lower() for term in ['warbler', 'sparrow', 'finch', 'thrush']):
                        color = '#00ff00'  # Green for songbirds
                    else:
                        color = '#808080'  # Gray for others

                    # Add marker
                    marker = CircleMarker(coords, color, 8)
                    m.add_marker(marker)

                except Exception as e:
                    print(f"DEBUG: Error processing observation: {str(e)}")
                    continue

            # Render map
            image = m.render()
            
            # Convert to base64 for embedding in email
            with io.BytesIO() as bio:
                image.save(bio, format='PNG')
                img_str = base64.b64encode(bio.getvalue()).decode()

            return img_str

        except Exception as e:
            print(f"DEBUG: Error creating static map: {str(e)}")
            import traceback
            print(f"DEBUG: Stack trace: {traceback.format_exc()}")
            return None

    def send_email(self, subject, header, ai_analysis, raw_data, map_path=None):
        """Send email with report sections and embedded static map"""
        try:
            print("DEBUG: Setting up email...")
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient']

            # Create static map
            map_image = self.create_static_map(self.get_recent_observations())

            # Create HTML version with embedded static map
            html_content = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; }}
                    pre {{ 
                        white-space: pre-wrap;
                        font-family: monospace;
                        margin: 10px 0;
                    }}
                    .map-container {{
                        margin: 20px 0;
                        padding: 10px;
                        border: 1px solid #ccc;
                        text-align: center;
                    }}
                    .map-image {{
                        max-width: 100%;
                        height: auto;
                    }}
                </style>
            </head>
            <body>
                <pre>{header}</pre>
                <pre>{ai_analysis}</pre>
                <div class="map-container">
                    <h2>Bird Observation Map</h2>
                    <img src="data:image/png;base64,{map_image}" class="map-image" alt="Bird Observation Map">
                    <p><small>Map Legend: Red = Raptors, Blue = Waterfowl, Green = Songbirds, Gray = Other Birds</small></p>
                </div>
                <pre>{raw_data}</pre>
            </body>
            </html>
            """

            # Create plain text version
            text_content = f"{header}\n{ai_analysis}\n{raw_data}"

            # Attach both versions
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            print("DEBUG: Connecting to SMTP server...")
            with smtplib.SMTP(self.email_config['smtp_server'], 
                            int(self.email_config['smtp_port'])) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                            self.email_config['sender_password'])
                server.send_message(msg)

            print("Email sent successfully!")
            return True

        except Exception as e:
            print(f"DEBUG: Error sending email: {str(e)}")
            print(f"DEBUG: Error type: {type(e)}")
            import traceback
            print(f"DEBUG: Stack trace: {traceback.format_exc()}")
            return False

    def generate_daily_report(self, species_list=None):
        observations = self.get_recent_observations()
        
        if not observations:
            return "No observations found in the last 14 days."
        
        # Build report sections
        header = f"Bird Sighting Report\n"
        header += f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
        header += f"Location: {self.active_location['name']} ({self.active_location['radius']} mile radius)\n\n"

        # AI Analysis section
        ai_analysis = "AI Analysis and Insights\n"
        ai_analysis += "=====================\n"
        ai_analysis += self.analyze_observations(observations) + "\n\n"

        # Raw observations section
        raw_data = "Raw Observations\n"
        raw_data += "===============\n"
        for obs in observations:
            raw_data += f"Species: {obs['comName']}\n"
            raw_data += f"Location: {obs['locName']}\n"
            raw_data += f"Date/Time: {obs['obsDt']}\n"
            raw_data += f"Count: {obs.get('howMany', 'Not specified')}\n"
            raw_data += "-" * 40 + "\n"

        # Send email with map
        subject = f"Bird Sighting Report - {datetime.now().strftime('%Y-%m-%d')}"
        self.send_email(subject, header, ai_analysis, raw_data)

        return header + ai_analysis + raw_data

    def set_location(self, name, latitude, longitude, radius):
        """Update the active location and save to config"""
        self.active_location = {
            'name': name,
            'latitude': float(latitude),
            'longitude': float(longitude),
            'radius': float(radius)
        }
        
        # Save to config file
        config = self._load_config()
        
        # Create new location section if it doesn't exist
        location_name = name.lower().replace(' ', '_')
        section_name = f'location_{location_name}'
        
        if not config.has_section(section_name):
            config.add_section(section_name)
        
        config[section_name]['name'] = name
        config[section_name]['latitude'] = str(latitude)
        config[section_name]['longitude'] = str(longitude)
        config[section_name]['radius'] = str(radius)
        
        # Update active location
        config['locations']['active_location'] = location_name
        
        # Save config
        with open('/Users/Mario/Documents/bird_tracker/config.ini', 'w') as f:
            config.write(f)

    def start_daily_reports(self):
        """Start the scheduler for daily reports with error handling"""
        try:
            scheduler = BackgroundScheduler()
            
            # Get email schedule from config
            hour = self.config.getint('email_schedule', 'hour', fallback=7)
            minute = self.config.getint('email_schedule', 'minute', fallback=0)
            
            # Schedule daily report
            scheduler.add_job(
                self._send_daily_report,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_report',
                name='Generate daily bird report',
                replace_existing=True,
                misfire_grace_time=3600  # Allow job to run up to 1 hour late
            )
            
            # Add error listener
            scheduler.add_listener(
                self._handle_scheduler_error,
                EVENT_JOB_ERROR | EVENT_JOB_MISSED
            )
            
            scheduler.start()
            logging.info(f"Scheduler started. Daily reports will be sent at {hour:02d}:{minute:02d}")
            return scheduler
        
        except Exception as e:
            logging.error(f"Failed to start scheduler: {str(e)}")
            return None

    def _handle_scheduler_error(self, event):
        """Handle scheduler errors and missed jobs"""
        if event.code == EVENT_JOB_ERROR:
            logging.error(f"Error in scheduled job: {event.job_id}")
            logging.error(f"Exception: {event.exception}")
            
            # Attempt to notify admin
            self.send_error_notification(
                f"Bird Tracker Scheduler Error: {event.job_id}",
                str(event.exception)
            )
        
        elif event.code == EVENT_JOB_MISSED:
            logging.warning(f"Missed scheduled job: {event.job_id}")
            # Attempt to run missed job if within last 24 hours
            if datetime.now() - event.scheduled_run_time < timedelta(days=1):
                self._send_daily_report()

    def _send_daily_report(self):
        """Wrapper for generate_daily_report with error handling"""
        try:
            self.generate_daily_report()
            logging.info("Daily report sent successfully")
        except Exception as e:
            logging.error(f"Error sending daily report: {str(e)}")
            self.send_error_notification(
                "Bird Tracker Daily Report Error",
                f"Failed to send daily report: {str(e)}"
            )

    def send_error_notification(self, subject, error_message):
        """Send error notification email to admin"""
        try:
            msg = MIMEText(f"Error occurred in Bird Tracker:\n\n{error_message}")
            msg['Subject'] = subject
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['admin_email']  # Add admin_email to config
            
            with smtplib.SMTP(self.email_config['smtp_server'], 
                             int(self.email_config['smtp_port'])) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                            self.email_config['sender_password'])
                server.send_message(msg)
        except Exception as e:
            logging.error(f"Failed to send error notification: {str(e)}")

    def update_email_schedule(self, hour, minute):
        """Update the email schedule in config and restart scheduler"""
        try:
            # Validate input
            hour = int(hour)
            minute = int(minute)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError("Invalid time")
            
            # Update config
            if not self.config.has_section('email_schedule'):
                self.config.add_section('email_schedule')
            
            self.config['email_schedule']['hour'] = str(hour)
            self.config['email_schedule']['minute'] = str(minute)
            
            # Save config
            with open('/Users/Mario/Documents/bird_tracker/config.ini', 'w') as f:
                self.config.write(f)
            
            # Restart scheduler
            if hasattr(self, 'scheduler') and self.scheduler:
                self.scheduler.shutdown()
            self.scheduler = self.start_daily_reports()
            
            return True
        except Exception as e:
            logging.error(f"Failed to update email schedule: {str(e)}")
            return False

    def test_email_configuration(self):
        """Test email configuration by sending a test email"""
        try:
            msg = MIMEText("This is a test email from your Bird Tracker application.")
            msg['Subject'] = 'Bird Tracker Email Test'
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient']
            
            with smtplib.SMTP(self.email_config['smtp_server'], 
                             self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                            self.email_config['sender_password'])
                server.send_message(msg)
            
            print("Test email sent successfully!")
            return True
        except Exception as e:
            print(f"Error sending test email: {str(e)}")
            return False

if __name__ == "__main__":
    try:
        print("DEBUG: Starting program...")
        print("DEBUG: Creating tracker instance...")
        tracker = BirdSightingTracker()
        
        print("DEBUG: Loading config...")
        print(f"DEBUG: Active location: {tracker.active_location}")
        
        print("\nGenerating bird sighting report...")
        report = tracker.generate_daily_report()
        print("\nReport Contents:")
        print(report)
        
    except Exception as e:
        print(f"ERROR: An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())
    finally:
        input("Press Enter to close this window...")