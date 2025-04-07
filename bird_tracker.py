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
import tempfile
from math import cos, sin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from models import User, Location

# Setup logging
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

class BirdSightingTracker:
    def __init__(self):
        load_dotenv()
        self.config = self._load_config()
        
        # Initialize with default values if environment variables are missing
        self.api_key = os.getenv('EBIRD_API_KEY')
        self.base_url = "https://api.ebird.org/v2"
        
        # Email config with defaults
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'sender_email': os.getenv('SMTP_USER', ''),
            'sender_password': os.getenv('SMTP_PASSWORD', ''),
            'admin_email': os.getenv('ADMIN_EMAIL', ''),
            'recipient': os.getenv('RECIPIENT_EMAIL', '')
        }
        
        # Set active location with defaults
        self.active_location = self._get_active_location()
        
        # Initialize Claude with the latest API version
        anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        if anthropic_api_key:
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
        else:
            logging.warning("ANTHROPIC_API_KEY not found, AI analysis will be limited")
            self.claude = None
        
        # Start daily report scheduler
        self.scheduler = self.start_daily_reports()
        
        # Initialize logger
        self.logger = logging.getLogger(__name__)
    
    def _load_config(self):
        """Load configuration from file or environment variables"""
        config = ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        
        # Try to load from config file first
        if config.read(config_path):
            logger.info("Config file loaded successfully")
            logger.info(f"Sections found: {config.sections()}")
            
            # Verify that the active location exists in the config
            if 'locations' in config and 'active_location' in config['locations']:
                active_location = config['locations']['active_location']
                location_section = f"location_{active_location}"
                if location_section not in config:
                    logger.warning(f"Active location section {location_section} not found, resetting to Cincinnati")
                    config['locations']['active_location'] = 'cincinnati'
                    with open(config_path, 'w') as configfile:
                        config.write(configfile)
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
        
        # Save the config file
        with open(config_path, 'w') as configfile:
            config.write(configfile)
        
        logger.info("Created config from environment variables")
        return config

    def _get_active_location(self):
        """Get the active location from the config"""
        try:
            active_location = self.config['locations']['active_location']
            location_section = f"location_{active_location}"
            
            if location_section in self.config:
                return {
                    'name': self.config[location_section]['name'],
                    'latitude': float(self.config[location_section]['latitude']),
                    'longitude': float(self.config[location_section]['longitude']),
                    'radius': float(self.config[location_section]['radius'])
                }
            else:
                # Try to find a matching location section
                for section in self.config.sections():
                    if section.startswith('location_'):
                        # Compare the normalized names
                        section_name = section.replace('location_', '').lower()
                        if section_name == active_location.lower():
                            return {
                                'name': self.config[section]['name'],
                                'latitude': float(self.config[section]['latitude']),
                                'longitude': float(self.config[section]['longitude']),
                                'radius': float(self.config[section]['radius'])
                            }
                
                # If no matching location found, reset to Cincinnati
                logger.warning(f"Location section {location_section} not found, resetting to Cincinnati")
                self.config['locations']['active_location'] = 'cincinnati'
                config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
                with open(config_path, 'w') as configfile:
                    self.config.write(configfile)
                
                return {
                    'name': 'Cincinnati',
                    'latitude': 39.1031,
                    'longitude': -84.5120,
                    'radius': 25
                }
        except Exception as e:
            logger.error(f"Error getting active location: {str(e)}")
            return None

    def set_location(self, name, latitude, longitude, radius):
        """Set a new active location"""
        try:
            # Format location name for config file
            location_key = name.lower().replace(' ', '_').replace(',', '_').replace('(', '').replace(')', '').replace("'", '')
            
            # Create a new location section
            location_section = f"location_{location_key}"
            if not self.config.has_section(location_section):
                self.config.add_section(location_section)
            
            # Update location details
            self.config[location_section]['name'] = name
            self.config[location_section]['latitude'] = str(latitude)
            self.config[location_section]['longitude'] = str(longitude)
            self.config[location_section]['radius'] = str(radius)
            
            # Set as active location
            self.config['locations']['active_location'] = location_key
            
            # Save config
            config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
            with open(config_path, 'w') as configfile:
                self.config.write(configfile)
            
            # Update active location in memory
            self.active_location = {
                'name': name,
                'latitude': float(latitude),
                'longitude': float(longitude),
                'radius': float(radius)
            }
            
            logger.info(f"Location updated to: {name}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting location: {str(e)}")
            return False

    def start_daily_reports(self):
        """Start the daily report scheduler"""
        try:
            scheduler = BackgroundScheduler()
            
            # Get schedule from config
            hour = int(self.config['email_schedule']['hour'])
            minute = int(self.config['email_schedule']['minute'])
            
            # Add job for daily reports
            scheduler.add_job(
                func=self.send_daily_report,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_report',
                name='Send daily bird sighting report',
                replace_existing=True
            )
            
            # Add error listener
            scheduler.add_listener(
                self._handle_job_error,
                EVENT_JOB_ERROR | EVENT_JOB_MISSED
            )
            
            scheduler.start()
            logger.info(f"Started daily report scheduler (runs at {hour:02d}:{minute:02d})")
            return scheduler
            
        except Exception as e:
            logger.error(f"Error starting daily reports: {str(e)}")
            return None

    def _handle_job_error(self, event):
        """Handle scheduler job errors"""
        if event.exception:
            logger.error(f"Job {event.job_id} failed: {str(event.exception)}")
            
            # Notify admin of failure
            if self.email_config['admin_email']:
                subject = f"Bird Tracker Job Error: {event.job_id}"
                body = f"The following error occurred:\n\n{str(event.exception)}"
                self.send_email(body, self.email_config['admin_email'], subject=subject)

    def send_daily_report(self):
        """Send daily report of bird sightings."""
        try:
            self.logger.info("Starting daily report generation")
            
            # Get recent observations
            observations = self.get_recent_observations()
            if not observations:
                self.logger.info("No observations to report")
                return
            
            # Format observations
            formatted_observations = self._format_observations(observations)
            
            # Get analysis
            analysis = self.analyze_recent_sightings(observations)
            
            # Prepare email content
            subject = f"Daily Bird Sighting Report - {datetime.now().strftime('%Y-%m-%d')}"
            body = f"""Bird Sighting Report for {self.active_location['name']}

{formatted_observations}

Analysis:
{analysis}

This report was generated automatically by the Bird Tracker application.
"""
            
            # Send email
            self.send_email(subject, body)
            self.logger.info("Daily report sent successfully")
            
        except Exception as e:
            self.logger.error(f"Error sending daily report: {str(e)}")
            raise

    def send_email(self, subject, body):
        """Send an email using configured SMTP settings."""
        try:
            # Check if email configuration exists
            if not self.config.has_section('email'):
                self.logger.error("Email configuration not found")
                raise ValueError("Email configuration not found")

            # Get email configuration
            smtp_server = self.config.get('email', 'smtp_server')
            smtp_port = self.config.getint('email', 'smtp_port')
            sender_email = self.config.get('email', 'sender_email')
            sender_password = self.config.get('email', 'sender_password')
            recipient_email = self.config.get('email', 'recipient_email')

            # Create message
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient_email

            # Send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            self.logger.info(f"Email sent successfully to {recipient_email}")

        except Exception as e:
            self.logger.error(f"Error sending email: {str(e)}")
            raise

    def analyze_recent_sightings(self, observations):
        """Analyze recent bird sightings and generate a report"""
        try:
            # Format observations for display
            formatted_observations = self._format_observations(observations)
            
            # If Claude is available, get AI analysis
            if self.claude:
                return self._get_ai_analysis(observations)
            else:
                return self._generate_basic_analysis(observations)
            
        except Exception as e:
            logger.error(f"Error analyzing sightings: {str(e)}")
            return f"Error analyzing sightings: {str(e)}"

    def _format_observations(self, observations):
        """Format bird observations into a readable string."""
        if not observations:
            return "No bird sightings found in the last 7 days."
        
        formatted_text = "Recent Bird Sightings:\n\n"
        for obs in observations:
            date = datetime.fromisoformat(obs['obsDt']).strftime('%Y-%m-%d')
            formatted_text += f"- {obs['comName']} (Scientific name: {obs['sciName']})\n"
            formatted_text += f"  Observed on: {date}\n"
            formatted_text += f"  Location: {obs['locName']}\n"
            if obs.get('howMany'):
                formatted_text += f"  Count: {obs['howMany']}\n"
            formatted_text += "\n"
        return formatted_text

    def _get_ai_analysis(self, observations):
        """Generate AI analysis of bird observations using Claude."""
        try:
            if not observations:
                return "No observations to analyze."
            
            if not self.claude:
                self.logger.warning("Claude client not initialized, skipping AI analysis")
                return None

            # Prepare the observation data for analysis
            observation_text = self._format_observations(observations)
            
            # Include location information
            location_info = ""
            if self.active_location:
                location_info = f"""Location: {self.active_location['name']}
                Latitude: {self.active_location['latitude']}
                Longitude: {self.active_location['longitude']}
                Search radius: {self.active_location['radius']} miles
                
                """
            
            prompt = f"""Please analyze these bird observations and provide insights in the following format:

            {location_info}
            {observation_text}
            
            Format your response EXACTLY as follows, with clear paragraph breaks between sections:
            
            1. Start with a main paragraph providing an overall summary of the observations. This should be a clear, well-structured paragraph that gives a comprehensive overview.
            
            2. After the main paragraph, add TWO blank lines before starting the bulleted sections.
            
            3. Then include three bulleted sections, each starting with a bullet point (•) and separated by ONE blank line:
               • Unusual or rare species for this location
               • Migratory species observed
               • Summary of Birds of Prey
            
            For each bulleted section:
            - List each species on a new line
            - Start each species with a hyphen (-)
            - Include the location in parentheses after each species
            - DO NOT include dates in the summary
            
            Example format:
            [Main summary paragraph goes here]

            • Unusual or rare species for this location:
            - Species Name (Location)
            - Another Species (Location)

            • Migratory species observed:
            - Species Name (Location)
            - Another Species (Location)

            • Summary of Birds of Prey:
            - Species Name (Location)
            - Another Species (Location)
            
            Make sure to:
            1. Use clear, well-structured paragraphs
            2. Include TWO blank lines after the main summary paragraph
            3. Include ONE blank line between each bulleted section
            4. Keep the main summary paragraph concise but informative
            5. Focus on the species and locations without dates
            6. Use proper bullet points and formatting for readability
            7. Ensure each section is visually distinct with proper spacing"""

            message = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.7,
                system="You are an expert ornithologist analyzing bird sighting data. Format your response with proper paragraphs and bullet points as requested.",
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract the text content from the response
            if hasattr(message, 'content'):
                if isinstance(message.content, list):
                    # Handle list of ContentBlock objects
                    text_content = ""
                    for block in message.content:
                        if hasattr(block, 'text'):
                            text_content += block.text + "\n"
                    return text_content.strip()
                elif hasattr(message.content, 'text'):
                    # Handle single ContentBlock object
                    return message.content.text
                elif isinstance(message.content, str):
                    # Handle string content
                    return message.content
                else:
                    # Try to convert to string if it's some other type
                    return str(message.content)
            else:
                return "Sorry, I couldn't generate a response."

        except Exception as e:
            self.logger.error(f"Error generating AI analysis: {str(e)}")
            return None

    def chat_with_ai(self, message):
        """Chat with the AI assistant about bird sightings."""
        try:
            if not self.claude:
                self.logger.warning("Claude client not initialized, cannot chat with AI")
                return "Sorry, the AI assistant is not available at the moment."
                
            # Get recent observations to provide context
            observations = self.get_recent_observations()
            observation_context = ""
            
            # Include location information
            location_info = ""
            if self.active_location:
                location_info = f"""Current location: {self.active_location['name']}
                Latitude: {self.active_location['latitude']}
                Longitude: {self.active_location['longitude']}
                Search radius: {self.active_location['radius']} miles
                
                """
            
            if observations:
                observation_context = f"""{location_info}
                Here are recent bird observations in the area:
                {self._format_observations(observations)}
                
                Please use this information to answer the user's question if relevant."""
            else:
                observation_context = f"""{location_info}
                No recent bird observations are available for this location."""
            
            # Create the prompt with the user's message and observation context
            prompt = f"""{observation_context}
            
            User question: {message}
            
            Please provide a helpful, informative response about birds and birdwatching. Format your response with:
            - Clear paragraphs for general information
            - Bullet points (•) for lists
            - Hyphens (-) for individual items in lists
            - Include locations and dates when relevant
            - Use proper spacing between sections"""
            
            # Send to Claude
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.7,
                system="You are a helpful birdwatching assistant. Provide accurate, informative responses about birds and birdwatching.",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract the text content from the response
            if hasattr(response, 'content'):
                if isinstance(response.content, list):
                    # Handle list of ContentBlock objects
                    text_content = ""
                    for block in response.content:
                        if hasattr(block, 'text'):
                            text_content += block.text + "\n"
                    return text_content.strip()
                elif hasattr(response.content, 'text'):
                    # Handle single ContentBlock object
                    return response.content.text
                elif isinstance(response.content, str):
                    # Handle string content
                    return response.content
                else:
                    # Try to convert to string if it's some other type
                    return str(response.content)
            else:
                return "Sorry, I couldn't generate a response."
            
        except Exception as e:
            self.logger.error(f"Error in chat_with_ai: {str(e)}")
            return f"Sorry, there was an error processing your request: {str(e)}"

    def _generate_basic_analysis(self, observations):
        """Generate a basic analysis of bird observations without AI."""
        if not observations:
            return "No observations to analyze."

        analysis = []
        species_count = len({obs['comName'] for obs in observations})
        total_birds = sum(obs.get('howMany', 1) for obs in observations)
        
        analysis.append(f"Summary of Bird Activity:")
        analysis.append(f"- Total unique species observed: {species_count}")
        analysis.append(f"- Total individual birds counted: {total_birds}")
        
        # Most frequently observed species
        species_frequency = {}
        for obs in observations:
            species = obs['comName']
            count = obs.get('howMany', 1)
            species_frequency[species] = species_frequency.get(species, 0) + count
        
        if species_frequency:
            most_common = max(species_frequency.items(), key=lambda x: x[1])
            analysis.append(f"- Most frequently observed species: {most_common[0]} ({most_common[1]} individuals)")
        
        # Date range
        dates = [datetime.fromisoformat(obs['obsDt']) for obs in observations]
        if dates:
            date_range = f"- Observation period: {min(dates).strftime('%Y-%m-%d')} to {max(dates).strftime('%Y-%m-%d')}"
            analysis.append(date_range)
        
        return "\n".join(analysis)

    def get_recent_observations(self):
        """Get recent bird observations from eBird API"""
        try:
            if not self.api_key:
                raise ValueError("eBird API key not found")
            
            # Get the most recent active location from the database
            active_location = Location.query.filter_by(is_active=True).first()
            
            if active_location:
                # Update the active_location property
                self.active_location = {
                    'name': active_location.name,
                    'latitude': active_location.latitude,
                    'longitude': active_location.longitude,
                    'radius': active_location.radius
                }
            
            if not self.active_location:
                raise ValueError("No active location configured")
            
            # Set up request parameters
            headers = {
                'X-eBirdApiToken': self.api_key
            }
            
            params = {
                'lat': self.active_location['latitude'],
                'lng': self.active_location['longitude'],
                'dist': self.active_location['radius'],
                'back': 7,  # Get observations from last 7 days
                'maxResults': 100
            }
            
            # Make request to eBird API
            url = f"{self.base_url}/data/obs/geo/recent"
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            
            # Parse response
            observations = response.json()
            
            # Sort observations by date (most recent first)
            observations.sort(key=lambda x: x['obsDt'], reverse=True)
            
            # Transform field names to match template expectations
            transformed_observations = []
            for obs in observations:
                transformed_obs = {
                    'comName': obs.get('comName', ''),
                    'sciName': obs.get('sciName', ''),
                    'howMany': obs.get('howMany', 0),
                    'locName': obs.get('locName', ''),
                    'obsDt': obs.get('obsDt', ''),
                    'lat': obs.get('lat', 0),
                    'lng': obs.get('lng', 0),
                    'subId': obs.get('subId', ''),
                    'userDisplayName': obs.get('userDisplayName', ''),
                    'obsValid': obs.get('obsValid', True),
                    'obsReviewed': obs.get('obsReviewed', False),
                    'locationPrivate': obs.get('locationPrivate', False),
                    'subnational2Code': obs.get('subnational2Code', ''),
                    'subnational2Name': obs.get('subnational2Name', ''),
                    'subnational1Code': obs.get('subnational1Code', ''),
                    'subnational1Name': obs.get('subnational1Name', ''),
                    'countryCode': obs.get('countryCode', ''),
                    'countryName': obs.get('countryName', ''),
                    'speciesCode': obs.get('speciesCode', ''),
                    'category': ''  # Will be set by the frontend
                }
                transformed_observations.append(transformed_obs)
            
            return transformed_observations
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting observations from eBird API: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error getting observations: {str(e)}")
            return None 