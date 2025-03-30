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
            # Get the active location
            active_location = self.get_current_location()
            if not active_location:
                logging.error("No active location found")
                return []

            # Construct the API request
            endpoint = f"{self.base_url}/data/obs/geo/recent"
            params = {
                'lat': active_location['latitude'],
                'lng': active_location['longitude'],
                'dist': 50,  # 50km radius
                'back': 7,   # Last 7 days
                'maxResults': 100
            }
            headers = {'X-eBirdApiToken': self.api_key}

            logging.info(f"Making eBird API request to {endpoint}")
            logging.info(f"API Key present: {'Yes' if self.api_key else 'No'}")
            if self.api_key:
                logging.info(f"API Key starts with: {self.api_key[:8]}...")

            response = requests.get(endpoint, params=params, headers=headers)
            logging.info(f"API Response Status Code: {response.status_code}")
            logging.info(f"API Response Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                observations = response.json()
                logging.info(f"Number of observations retrieved: {len(observations)}")
                if observations:
                    logging.info(f"First observation: {json.dumps(observations[0], indent=2)}")
                return observations
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
                        model="claude-3-opus-20240229",
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