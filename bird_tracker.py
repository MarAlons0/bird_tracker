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
import json

# Setup logging
logger = logging.getLogger(__name__)

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
        
        # Initialize Claude with the latest API version
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        print(f"DEBUG: Initializing Anthropic client with key starting with: {anthropic_api_key[:8]}...")
        self.claude = Anthropic(api_key=anthropic_api_key)
        
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
    
    def get_current_location(self):
        """Return the current tracking location"""
        try:
            # Get the active location section name from config
            active_location = self.config['locations']['active_location']
            section_name = f'location_{active_location}'
            
            # Get location details from config
            if self.config.has_section(section_name):
                return {
                    'name': self.config[section_name]['name'],
                    'latitude': float(self.config[section_name]['latitude']),
                    'longitude': float(self.config[section_name]['longitude']),
                    'radius': float(self.config[section_name]['radius'])
                }
            else:
                # Fall back to active_location if section not found
                return self.active_location
                
        except Exception as e:
            print(f"Error getting current location: {str(e)}")
            # Fall back to active_location if any error occurs
            return self.active_location
    
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
        """Get recent bird sightings within radius of active location"""
        try:
            endpoint = f"{self.base_url}/data/obs/geo/recent"
            headers = {'X-eBirdApiToken': self.api_key}
            params = {
                'lat': float(self.active_location['latitude']),
                'lng': float(self.active_location['longitude']),
                'dist': float(self.active_location['radius']),
                'back': 21,
                'maxResults': 1000
            }
            
            logger.debug(f"Making eBird API request to {endpoint}")
            response = requests.get(endpoint, headers=headers, params=params)
            logger.debug(f"API Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                observations = response.json()
                logger.info(f"Successfully retrieved {len(observations)} observations")
                return observations or []  # Return empty list instead of None
            else:
                logger.error(f"eBird API Error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error getting observations: {e}")
            return []
    
    def analyze_observations(self, observations):
        try:
            if not observations:
                logger.info("No observations to analyze")
                return "<p>No recent bird sightings found in this area.</p>"
            
            logger.info(f"Analyzing {len(observations)} observations for {self.active_location['name']}")
            
            # Create a summary of observations for the prompt
            species_count = len(set(obs['comName'] for obs in observations))
            common_species = [
                obs['comName'] for obs in observations 
                if observations.count(obs['comName']) > 2
            ][:5]  # Get top 5 most common
            
            prompt = f"""Analyze these bird sightings from {self.active_location['name']}:

Location: {self.active_location['name']}
Total Species: {species_count}
Total Observations: {len(observations)}
Common Species: {', '.join(set(common_species))}
Time period: Last 21 days

Please provide a brief analysis focusing on:
1. Notable patterns or trends
2. Rare or unusual species
3. Common species activity

Format as HTML with paragraphs and lists.
"""
            logger.debug(f"Sending prompt to Claude: {prompt[:200]}...")
            
            try:
                response = self.claude.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }],
                    timeout=45  # Increase timeout
                )
                logger.info("Successfully received response from Claude")
                return response.content[0].text
                
            except Exception as api_error:
                logger.error(f"Claude API error: {api_error}")
                return self._generate_basic_analysis(observations)
                
        except Exception as e:
            logger.error(f"Error in analyze_observations: {e}")
            return None

    def _generate_basic_analysis(self, observations):
        """Generate a basic analysis when AI is unavailable"""
        species_count = len(set(obs['comName'] for obs in observations))
        total_sightings = len(observations)
        
        # Get most common species
        species_freq = {}
        for obs in observations:
            species_freq[obs['comName']] = species_freq.get(obs['comName'], 0) + 1
        common_species = sorted(species_freq.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return f"""
        <div class='basic-analysis'>
            <h3>Basic Analysis</h3>
            <p>In the last 21 days around {self.active_location['name']}:</p>
            <ul>
                <li>{total_sightings} total bird sightings recorded</li>
                <li>{species_count} different species observed</li>
            </ul>
            <h4>Most Frequently Observed Species:</h4>
            <ul>
                {' '.join(f'<li>{species} ({count} sightings)</li>' for species, count in common_species)}
            </ul>
            <p class='alert alert-info'>
                Note: Detailed AI analysis is currently unavailable. 
                Basic statistics are shown instead.
            </p>
        </div>
        """

    def create_static_map(self, observations):
        """Create a static map of bird observations using Google Maps"""
        try:
            base_url = "https://maps.googleapis.com/maps/api/staticmap"
            
            # Set map parameters
            params = {
                'center': f"{self.active_location['latitude']},{self.active_location['longitude']}",
                'zoom': '11',
                'size': '800x600',
                'maptype': 'roadmap',
                'key': os.getenv('GOOGLE_MAPS_API_KEY')
            }
            
            # Add markers for each observation
            markers = []
            for obs in observations:
                try:
                    lat = None
                    lng = None
                    
                    # Extract coordinates from location string
                    if '(' in obs['locName'] and ')' in obs['locName']:
                        coords_text = obs['locName'].split('(')[-1].split(')')[0]
                        try:
                            lat, lng = map(float, coords_text.split(','))
                            # Color code by bird type
                            color = 'red' if any(term in obs['comName'].lower() 
                                              for term in ['hawk', 'eagle', 'owl', 'falcon']) else 'blue'
                            markers.append(f"color:{color}|{lat},{lng}")
                        except:
                            continue
                
                except Exception as e:
                    print(f"DEBUG: Error processing observation for map: {str(e)}")
                    continue
            
            if markers:
                params['markers'] = markers
            
            print("DEBUG: Making map request...")
            response = requests.get(base_url, params=params)
            
            if response.status_code == 200:
                print("DEBUG: Map generated successfully")
                return base64.b64encode(response.content).decode()
            else:
                raise Exception(f"Map API returned status code {response.status_code}")
                
        except Exception as e:
            print(f"DEBUG: Error creating map: {str(e)}")
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
                    body {{ 
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                    }}
                    .header {{
                        text-align: center;
                        margin-bottom: 30px;
                    }}
                    .main-title {{
                        font-size: 24px;
                        font-weight: bold;
                        margin-bottom: 5px;
                    }}
                    .subtitle {{
                        font-size: 16px;
                        color: #666;
                        margin-bottom: 20px;
                    }}
                    .analysis {{
                        margin: 20px 0;
                        padding: 0 20px;
                    }}
                    .analysis ol {{
                        margin-bottom: 20px;
                    }}
                    .analysis li {{
                        margin-bottom: 10px;
                    }}
                    .analysis ul {{
                        margin-top: 5px;
                        margin-left: 20px;
                    }}
                    pre {{ 
                        white-space: pre-wrap;
                        font-family: monospace;
                        margin: 10px 0;
                        padding: 10px;
                        background-color: #f8f9fa;
                        border-radius: 4px;
                    }}
                    .map-container {{
                        margin: 20px 0;
                        padding: 10px;
                        border: 1px solid #ddd;
                        border-radius: 4px;
                        text-align: center;
                        background-color: #f8f9fa;
                    }}
                    .map-image {{
                        max-width: 100%;
                        height: auto;
                        border-radius: 4px;
                    }}
                    .map-legend {{
                        font-size: 14px;
                        color: #666;
                        margin-top: 10px;
                    }}
                    .raw-data {{
                        margin-top: 30px;
                        border-top: 1px solid #ddd;
                        padding-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <div class="main-title">Mario's Bird Tracker</div>
                    <div class="subtitle">(powered by eBird)</div>
                </div>
                
                <div class="analysis">
                    {self._format_ai_analysis(ai_analysis)}
                </div>

                <div class="map-container">
                    <h2>Bird Observation Map</h2>
                    <img src="data:image/png;base64,{map_image}" class="map-image" alt="Bird Observation Map">
                    <p class="map-legend">Map Legend: Red = Birds of Prey, Blue = Other Birds</p>
                </div>

                <div class="raw-data">
                    <h3>Raw Observation Data</h3>
                    <pre>{raw_data}</pre>
                </div>
            </body>
            </html>
            """

            # Create plain text version
            text_content = f"""
            MARIO'S BIRD TRACKER
            (powered by eBird)

            {ai_analysis}

            {raw_data}
            """

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
        with open('config.ini', 'w') as f:
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
            with open('config.ini', 'w') as f:
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

    def _format_ai_analysis(self, analysis):
        """Format AI analysis with proper HTML structure"""
        sections = analysis.split('\n\n')  # Split on double newlines
        formatted = []
        
        for section in sections:
            if not section.strip():
                continue
            
            lines = section.split('\n')
            if not lines:
                continue
            
            # Handle section header
            header = lines[0].strip(':')
            formatted.append(f'<h3 class="mt-4 mb-3">{header}</h3>')
            
            # Handle bullet points
            bullets = []
            current_paragraph = []
            
            for line in lines[1:]:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('-'):
                    bullets.append(f'<li class="mb-2">{line.strip("- ")}</li>')
                elif line.strip():
                    current_paragraph.append(line)
            
            # Add any paragraph text first
            if current_paragraph:
                formatted.append(f'<p class="mb-3">{"<br>".join(current_paragraph)}</p>')
            
            # Then add bullet points
            if bullets:
                formatted.append('<ul class="list-group list-group-flush mb-4">\n' + 
                               '\n'.join(bullets) + 
                               '\n</ul>')
        
        return '\n'.join(formatted)

    @staticmethod
    def format_observations_for_analysis(observations):
        """Format observations for Claude analysis"""
        if not observations:
            return "No observations available"
        
        formatted = []
        for obs in observations:
            formatted.append(f"- {obs['comName']} ({obs['sciName']}) - Count: {obs['howMany']} - Date: {obs['obsDt']}")
        
        return "\n".join(formatted)

    def send_daily_report(self):
        """Send daily report email"""
        try:
            report = self.generate_daily_report()
            
            msg = MIMEText(report)
            msg['Subject'] = f'Bird Tracker Daily Report - {datetime.now().strftime("%Y-%m-%d")}'
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['admin_email']  # Use admin_email for recipient
            
            with smtplib.SMTP(self.email_config['smtp_server'], 
                             self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], 
                           self.email_config['sender_password'])
                server.send_message(msg)
        except Exception as e:
            print(f"Error sending daily report: {str(e)}")

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