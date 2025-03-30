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
import time
import random

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
        
        # Ensure API key starts with 'sk-ant'
        if not anthropic_api_key.startswith('sk-ant'):
            anthropic_api_key = f"sk-ant-{anthropic_api_key}"
        
        logging.info(f"Initializing Anthropic client with key starting with: {anthropic_api_key[:8]}...")
        
        # Create a custom httpx client without proxies
        http_client = httpx.Client(
            base_url="https://api.anthropic.com",
            headers={
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
        )
        
        self.claude = Anthropic(
            api_key=anthropic_api_key,
            http_client=http_client
        )
        
        # Start daily report scheduler
        self.scheduler = self.start_daily_reports()
    
    def _load_config(self):
        """Load configuration from file or environment variables"""
        config = ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        
        # Try to load from config file first
        if config.read(config_path):
            logger.info("Config file loaded successfully")
            logger.info(f"Sections found: {config.sections()}")
            return config
            
        # If no config file, use environment variables
        logger.info("Config file not found, using environment variables")
        config.add_section('locations')
        config.add_section('email_schedule')
        
        # Get values from environment with defaults
        config['locations']['active_location'] = os.getenv('DEFAULT_LOCATION', 'cincinnati')
        config['email_schedule']['hour'] = os.getenv('EMAIL_SCHEDULE_HOUR', '7')
        config['email_schedule']['minute'] = os.getenv('EMAIL_SCHEDULE_MINUTE', '0')
        
        # Add location section with default values
        location_section = f"location_{config['locations']['active_location']}"
        config.add_section(location_section)
        config[location_section]['name'] = os.getenv('DEFAULT_LOCATION_NAME', 'Cincinnati')
        config[location_section]['latitude'] = os.getenv('DEFAULT_LATITUDE', '39.1031')
        config[location_section]['longitude'] = os.getenv('DEFAULT_LONGITUDE', '-84.5120')
        config[location_section]['radius'] = os.getenv('DEFAULT_RADIUS', '25')
        
        logger.info("Created config from environment variables")
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
    
    def get_recent_observations(self):
        """Get recent bird observations from eBird API."""
        try:
            # Use active_location directly instead of get_current_location
            if not self.active_location:
                logging.error("No active location found")
                return []

            # Construct the API request
            endpoint = f"{self.base_url}/data/obs/geo/recent"
            params = {
                'lat': self.active_location['latitude'],
                'lng': self.active_location['longitude'],
                'dist': 50,  # 50km radius
                'back': 7,   # Last 7 days
                'maxResults': 100
            }
            headers = {'X-eBirdApiToken': self.api_key}

            logging.info(f"Making eBird API request to {endpoint}")
            logging.info(f"Using coordinates: {self.active_location['latitude']}, {self.active_location['longitude']}")
            logging.info(f"API Key present: {'Yes' if self.api_key else 'No'}")
            if self.api_key:
                logging.info(f"API Key starts with: {self.api_key[:8]}...")

            response = requests.get(endpoint, params=params, headers=headers)
            logging.info(f"API Response Status Code: {response.status_code}")
            
            if response.status_code == 200:
                observations = response.json()
                logging.info(f"Number of observations retrieved: {len(observations)}")
                
                # Validate and log coordinates
                valid_observations = []
                for obs in observations:
                    try:
                        lat = float(obs.get('lat'))
                        lng = float(obs.get('lng'))
                        if -90 <= lat <= 90 and -180 <= lng <= 180:
                            valid_observations.append(obs)
                            logging.info(f"Valid observation: {obs.get('comName', 'Unknown')} at {lat}, {lng}")
                        else:
                            logging.warning(f"Invalid coordinates for observation: {obs.get('comName', 'Unknown')}")
                    except (ValueError, TypeError) as e:
                        logging.warning(f"Error processing coordinates for observation: {str(e)}")
                
                logging.info(f"Number of valid observations: {len(valid_observations)}")
                return valid_observations
            else:
                logging.error(f"Error from eBird API: {response.status_code} - {response.text}")
                return []
        except Exception as e:
            logging.error(f"Error getting recent observations: {str(e)}")
            return []
    
    def analyze_observations(self):
        try:
            logging.info("Starting AI analysis of observations")
            logging.info(f"Using API key: {'Present' if self.api_key else 'Missing'}")
            
            if not self.get_recent_observations():
                logging.warning("No observations to analyze")
                return self._generate_basic_analysis()

            observations_text = self.format_observations_for_analysis(self.get_recent_observations())
            logging.info(f"Formatted observations for analysis: {observations_text[:100]}...")

            # Get location information
            location_name = self.active_location['name']
            location_radius = self.active_location['radius']
            
            # Try up to 3 times with exponential backoff
            max_retries = 3
            base_delay = 2  # Increased base delay to 2 seconds
            
            for attempt in range(max_retries):
                try:
                    # Add a small random delay between attempts to avoid thundering herd
                    if attempt > 0:
                        random_delay = random.uniform(0.5, 1.5)
                        time.sleep(random_delay)
                    
                    response = self.claude.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=1000,
                        temperature=0.7,
                        messages=[
                            {
                                "role": "user",
                                "content": f"""As an expert naturalist with extensive experience in avian ecology and behavior, analyze these bird sightings from {location_name} (within a {location_radius}-mile radius) and provide a concise summary in the following format:

1. Overview: A brief summary of the most significant observations and patterns, focusing on ecological significance and behavioral patterns specific to this location.
2. Trends: Compare with previous week's sightings, noting any notable changes in species composition, migration patterns, or behavioral shifts in this geographic area.
3. Birds of Prey: Focus on raptor sightings, their hunting behaviors, and ecological roles in the local ecosystem of {location_name}.
4. Notable Sightings: Highlight any rare or unusual species observed, with emphasis on their ecological significance and potential implications for local biodiversity in this region.

Observations:
{observations_text}"""
                            }
                        ]
                    )
                    logging.info("Successfully received response from Claude API")
                    logging.debug(f"Raw response: {response}")
                    
                    analysis = response.content[0].text
                    if not analysis or len(analysis.strip()) < 50:
                        logging.warning("Received empty or very short analysis from Claude API")
                        return self._generate_basic_analysis()
                    
                    return self._format_ai_analysis(analysis)
                    
                except anthropic.NotFoundError as e:
                    logging.error(f"Model not found: {str(e)}")
                    return self._generate_basic_analysis()
                except anthropic.AuthenticationError as e:
                    logging.error(f"Authentication error: {str(e)}")
                    return self._generate_basic_analysis()
                except anthropic.RateLimitError as e:
                    logging.error(f"Rate limit exceeded: {str(e)}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logging.info(f"Rate limit hit, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    return self._generate_basic_analysis()
                except anthropic.APIError as e:
                    logging.error(f"API error: {str(e)}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logging.info(f"API error, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    return self._generate_basic_analysis()
                except Exception as e:
                    logging.error(f"Error calling Claude API: {str(e)}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)  # Exponential backoff
                        logging.info(f"Unexpected error, retrying in {delay} seconds...")
                        time.sleep(delay)
                        continue
                    return self._generate_basic_analysis()
            
            logging.warning("All retry attempts failed, returning basic analysis")
            return self._generate_basic_analysis()
                
        except Exception as e:
            logging.error(f"Error in analyze_observations: {str(e)}")
            return self._generate_basic_analysis()
    
    def start_daily_reports(self):
        """Start the scheduler for daily reports"""
        try:
            scheduler = BackgroundScheduler()
            
            # Get schedule from config
            hour = self.config['email_schedule'].get('hour', '7')
            minute = self.config['email_schedule'].get('minute', '0')
            
            # Add the job
            scheduler.add_job(
                func=self.send_daily_report,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_report',
                name='Send daily bird report',
                replace_existing=True
            )
            
            # Add error listeners
            scheduler.add_listener(self._handle_job_error, EVENT_JOB_ERROR)
            scheduler.add_listener(self._handle_job_missed, EVENT_JOB_MISSED)
            
            # Start the scheduler
            scheduler.start()
            logging.info(f"Scheduler started. Daily report scheduled for {hour}:{minute}")
            return scheduler
            
        except Exception as e:
            logging.error(f"Error starting scheduler: {str(e)}")
            return None
            
    def _handle_job_error(self, event):
        """Handle job execution errors"""
        logging.error(f"Error executing job {event.job_id}: {str(event.exception)}")
        
    def _handle_job_missed(self, event):
        """Handle missed job executions"""
        logging.warning(f"Job {event.job_id} was missed!") 
    
    def send_daily_report(self):
        """Send daily bird sighting report via email"""
        try:
            # Get recent observations
            observations = self.get_recent_observations()
            if not observations:
                logging.warning("No observations to report")
                return
                
            # Generate AI analysis
            analysis = self.analyze_observations()
            
            # Create static map
            map_image = self.create_static_map(observations)
            
            # Send email with report
            self.send_email(analysis, map_image)
            logging.info("Daily report sent successfully")
            
        except Exception as e:
            logging.error(f"Error sending daily report: {str(e)}")
            
    def create_static_map(self, observations):
        """Create a static map with observation markers"""
        try:
            # Create a map centered on the active location
            m = StaticMap(300, 300, url_template='https://tile.openstreetmap.org/{z}/{x}/{y}.png')
            
            # Add markers for each observation
            for obs in observations:
                try:
                    lat = float(obs.get('lat'))
                    lng = float(obs.get('lng'))
                    if -90 <= lat <= 90 and -180 <= lng <= 180:
                        marker = CircleMarker(
                            (lng, lat),
                            fill='red',
                            radius=5,
                            stroke_width=1,
                            stroke_color='white'
                        )
                        m.add_marker(marker)
                except (ValueError, TypeError) as e:
                    logging.warning(f"Error adding marker for observation: {str(e)}")
                    continue
            
            # Render the map
            image = m.render()
            
            # Convert to base64
            buffered = io.BytesIO()
            image.save(buffered, format="PNG")
            logging.info("Map successfully created and encoded")
            return base64.b64encode(buffered.getvalue()).decode()
            
        except Exception as e:
            logging.error(f"Error creating map: {str(e)}")
            return None
            
    def send_email(self, analysis, map_image=None):
        """Send email with analysis and optional map"""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['Subject'] = f"Bird Sighting Report for {self.active_location['name']}"
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['recipient']
            
            # Add analysis text
            msg.attach(MIMEText(analysis, 'html'))
            
            # Add map if available
            if map_image:
                map_part = MIMEText(f'<img src="data:image/png;base64,{map_image}">', 'html')
                msg.attach(map_part)
            
            # Send email
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)
                
            logging.info("Email sent successfully")
            
        except Exception as e:
            logging.error(f"Error sending email: {str(e)}")
            
    def _generate_basic_analysis(self):
        """Generate a basic analysis when AI analysis fails"""
        try:
            observations = self.get_recent_observations()
            if not observations:
                return "<div class='alert alert-warning'>No observations found in the past week.</div>"
                
            # Count total observations and birds
            total_observations = len(observations)
            total_birds = sum(obs.get('howMany', 1) for obs in observations)
            
            # Count unique species
            species = set(obs['speciesCode'] for obs in observations)
            species_count = len(species)
            
            # Find most common species
            species_counts = defaultdict(int)
            for obs in observations:
                species_counts[obs['comName']] += obs.get('howMany', 1)
            common_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            
            # Count birds of prey
            raptors = [obs for obs in observations if any(term in obs.get('sciName', '').lower() 
                      for term in ['buteo', 'accipiter', 'falco', 'aquila', 'haliaeetus'])]
            
            # Find unusual sightings (single observations of species)
            unusual = [obs['comName'] for obs in observations 
                      if list(obs['comName'] for obs in observations).count(obs['comName']) == 1]
            
            # Format the analysis as HTML
            analysis = f"""
            <h3>Bird Sighting Report for {self.active_location['name']}</h3>
            <p>In the past week:</p>
            <ul>
                <li>Total observations: {total_observations}</li>
                <li>Total birds counted: {total_birds}</li>
                <li>Unique species: {species_count}</li>
            </ul>
            
            <h4>Most Common Species:</h4>
            <ul>
                {"".join(f"<li>{name}: {count}</li>" for name, count in common_species)}
            </ul>
            
            <h4>Birds of Prey:</h4>
            <ul>
                {"".join(f"<li>{obs['comName']}</li>" for obs in raptors) if raptors else "<li>No raptors observed</li>"}
            </ul>
            
            <h4>Unusual Sightings:</h4>
            <ul>
                {"".join(f"<li>{name}</li>" for name in unusual) if unusual else "<li>No unusual sightings</li>"}
            </ul>
            """
            
            return analysis
            
        except Exception as e:
            logging.error(f"Error generating basic analysis: {str(e)}")
            return "<div class='alert alert-danger'>Error generating analysis.</div>"

    def format_observations_for_analysis(self, observations):
        """Format observations for AI analysis"""
        try:
            if not observations:
                return "No recent observations found."
            
            formatted_observations = []
            for obs in observations:
                # Format the date
                obs_date = datetime.strptime(obs.get('obsDt', ''), '%Y-%m-%d %H:%M')
                date_str = obs_date.strftime('%B %d, %Y at %I:%M %p')
                
                # Get location details
                lat = obs.get('lat', 'N/A')
                lng = obs.get('lng', 'N/A')
                location = f"{lat}, {lng}"
                
                # Get count and details
                count = obs.get('howMany', 1)
                details = []
                if obs.get('behavior'):
                    details.append(f"Behavior: {obs['behavior']}")
                if obs.get('age'):
                    details.append(f"Age: {obs['age']}")
                if obs.get('sex'):
                    details.append(f"Sex: {obs['sex']}")
                
                # Format the observation
                obs_str = f"{obs.get('comName', 'Unknown species')} ({count})"
                if details:
                    obs_str += f" - {', '.join(details)}"
                obs_str += f" at {location} on {date_str}"
                
                formatted_observations.append(obs_str)
            
            return "\n".join(formatted_observations)
            
        except Exception as e:
            logger.error(f"Error formatting observations: {str(e)}")
            return "Error formatting observations for analysis."

    def generate_ai_analysis(self):
        """Generate AI analysis of recent bird observations"""
        try:
            # Get recent observations
            observations = self.get_recent_observations()
            if not observations:
                return '<div class="alert alert-info">No recent observations found.</div>'
            
            # Format observations for analysis
            formatted_observations = self.format_observations_for_analysis(observations)
            
            # Prepare the prompt for Claude
            prompt = f"""You are an expert ornithologist and birding guide. Please analyze these recent bird observations and provide a detailed report that includes:

1. A general summary of the observations
2. Notable species or unexpected sightings based on location and time of year
3. A recount of birds of prey observed
4. Recommendations for birders in this area

Here are the observations:

{formatted_observations}

Please provide a well-structured analysis that would be helpful for both casual birders and experienced ornithologists. Format your response in HTML with appropriate tags for better readability."""

            # Generate analysis using Claude
            max_retries = 3
            base_delay = 2  # Base delay in seconds
            
            for attempt in range(max_retries):
                try:
                    response = self.claude.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=1000,
                        temperature=0.7,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    
                    # Extract the analysis from the response
                    analysis = response.content[0].text
                    
                    # Ensure the analysis is properly formatted HTML
                    if not analysis.strip().startswith('<'):
                        analysis = f'<div class="analysis-content">{analysis}</div>'
                    
                    return analysis
                    
                except anthropic.NotFoundError as e:
                    logger.error(f"Model not found: {str(e)}")
                    return self._generate_basic_analysis()
                except anthropic.AuthenticationError as e:
                    logger.error(f"Authentication error: {str(e)}")
                    return self._generate_basic_analysis()
                except anthropic.RateLimitError as e:
                    logger.error(f"Rate limit exceeded: {str(e)}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limit hit, retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        continue
                    return self._generate_basic_analysis()
                except anthropic.APIError as e:
                    logger.error(f"API error: {str(e)}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"API error, retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        continue
                    return self._generate_basic_analysis()
                except Exception as e:
                    logger.error(f"Error calling Claude API: {str(e)}")
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Unexpected error, retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                        continue
                    return self._generate_basic_analysis()
            
            return self._generate_basic_analysis()
            
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return self._generate_basic_analysis()

    def set_location(self, name, latitude, longitude, radius):
        """Update the active location"""
        try:
            # Update the active location
            self.active_location = {
                'name': name,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'radius': float(radius)
            }
            
            # Update the config file
            section_name = f"location_{name.lower().replace(' ', '_')}"
            if not self.config.has_section(section_name):
                self.config.add_section(section_name)
            
            self.config[section_name]['name'] = name
            self.config[section_name]['latitude'] = str(latitude)
            self.config[section_name]['longitude'] = str(longitude)
            self.config[section_name]['radius'] = str(radius)
            
            # Update the active location in the locations section
            self.config['locations']['active_location'] = name.lower().replace(' ', '_')
            
            # Save the config file
            config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
            with open(config_path, 'w') as f:
                self.config.write(f)
            
            logging.info(f"Location updated to {name} ({latitude}, {longitude}) with radius {radius} miles")
            logging.info(f"Active location is now: {self.active_location}")
            
            # Force a refresh of observations for the new location
            self.get_recent_observations()
            
            return True
            
        except Exception as e:
            logging.error(f"Error updating location: {str(e)}")
            return False

    def chat_with_ai(self, message):
        """Handle chat interactions with Claude"""
        try:
            # Get recent observations for context
            observations = self.get_recent_observations()
            if not observations:
                return "I don't have any recent bird observations to analyze. Please try again later."
            
            # Format observations for context
            formatted_observations = self.format_observations_for_analysis(observations)
            
            # Prepare the prompt for Claude
            prompt = f"""You are an expert ornithologist and birding guide. You have access to recent bird observations from {self.active_location['name']} (within a {self.active_location['radius']}-mile radius).

Recent observations:
{formatted_observations}

User question: {message}

Please provide a helpful response based on the recent observations and your expertise. If the question is about specific species or behaviors not mentioned in the observations, you can still provide general information about those topics."""

            # Generate response using Claude
            max_retries = 3
            base_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.claude.messages.create(
                        model="claude-3-7-sonnet-20250219",
                        max_tokens=1000,
                        temperature=0.7,
                        messages=[{
                            "role": "user",
                            "content": prompt
                        }]
                    )
                    
                    # Extract the response
                    return response.content[0].text
                    
                except Exception as e:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f} seconds...")
                        time.sleep(delay)
                    else:
                        logger.error(f"All {max_retries} attempts failed. Last error: {str(e)}")
                        return "I apologize, but I encountered an error while processing your question. Please try again later."
            
        except Exception as e:
            logger.error(f"Error in chat_with_ai: {str(e)}")
            return "I apologize, but I encountered an error while processing your question. Please try again later."

    def _format_ai_analysis(self, analysis):
        """Format the AI analysis into HTML"""
        try:
            # If the analysis is already HTML, return it
            if analysis.strip().startswith('<'):
                return analysis
            
            # Otherwise, wrap it in HTML tags
            formatted = '<div class="analysis-content">'
            formatted += analysis.replace('\n', '<br>')
            formatted += '</div>'
            return formatted
            
        except Exception as e:
            logging.error(f"Error formatting analysis: {str(e)}")
            return f"<div class='alert alert-danger'>Error formatting analysis: {str(e)}</div>" 