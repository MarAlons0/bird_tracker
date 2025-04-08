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
from models import User, Location, UserPreferences

# Setup logging
logger = logging.getLogger(__name__)

# Initialize SQLAlchemy
db = SQLAlchemy()

class BirdSightingTracker:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.config = self._load_config()
        self.active_location = None
        self.claude = None
        self._initialize_claude()
        self._load_default_location()
        self.scheduler = None
        self._setup_scheduler()
        
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
        config['email_schedule']['day'] = os.getenv('EMAIL_SCHEDULE_DAY', '5')
        
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

    def _load_default_location(self):
        """Load the default location from config"""
        try:
            if 'location_cincinnati' in self.config:
                loc = self.config['location_cincinnati']
                self.active_location = {
                    'name': 'Cincinnati',
                    'latitude': float(loc['latitude']),
                    'longitude': float(loc['longitude']),
                    'radius': float(loc['radius'])
                }
                self.logger.info(f"Loaded default location: {self.active_location['name']}")
        except Exception as e:
            self.logger.error(f"Error loading default location: {str(e)}")
            self.active_location = None

    def set_location(self, user_id=None, name=None, lat=None, lng=None, radius=None):
        """Set the active location, supporting both user-specific and global locations"""
        try:
            if user_id is not None:
                # User-specific location
                from models import UserPreferences, Location, db
                
                self.logger.info(f"Setting user-specific location for user {user_id}: {name} ({lat}, {lng}, radius={radius})")
                
                try:
                    # Get or create user preferences
                    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
                    if not prefs:
                        self.logger.info(f"Creating new UserPreferences for user {user_id}")
                        prefs = UserPreferences(user_id=user_id)
                        db.session.add(prefs)
                        db.session.flush()  # Get the ID for the new preferences
                    
                    # Deactivate all existing locations for this user
                    Location.query.filter_by(user_id=user_id).update({'is_active': False})
                    db.session.flush()
                    
                    # Create a new location for the user
                    self.logger.info(f"Creating new location for user {user_id}")
                    location = Location(
                        name=name,
                        latitude=lat,
                        longitude=lng,
                        radius=radius,
                        is_active=True,
                        user_id=user_id
                    )
                    db.session.add(location)
                    db.session.flush()  # Get the ID for the new location
                    
                    # Update user preferences with the new location
                    prefs.active_location_id = location.id
                    
                    # Commit all changes
                    db.session.commit()
                    self.logger.info(f"Successfully set location for user {user_id}: {name}")
                    return True
                    
                except Exception as e:
                    self.logger.error(f"Error setting user-specific location: {str(e)}", exc_info=True)
                    db.session.rollback()
                    return False
            else:
                # Global location (backward compatibility)
                self.logger.info(f"Setting global location: {name} ({lat}, {lng}, radius={radius})")
                self.active_location = {
                    'name': name,
                    'latitude': lat,
                    'longitude': lng,
                    'radius': radius
                }
                return True
                
        except Exception as e:
            self.logger.error(f"Error in set_location: {str(e)}", exc_info=True)
            if 'db' in locals():
                db.session.rollback()
            return False

    def get_active_location(self, user_id=None):
        """Get the active location, supporting both user-specific and global locations"""
        try:
            if user_id is not None:
                # Try to get user-specific location
                from models import UserPreferences, Location, db
                
                self.logger.info(f"Getting active location for user {user_id}")
                
                try:
                    # Get user preferences and active location
                    prefs = UserPreferences.query.filter_by(user_id=user_id).first()
                    if prefs and prefs.active_location_id:
                        location = Location.query.get(prefs.active_location_id)
                        if location and location.is_active:
                            self.logger.info(f"Found active location for user {user_id}: {location.name}")
                            return {
                                'name': location.name,
                                'latitude': location.latitude,
                                'longitude': location.longitude,
                                'radius': location.radius
                            }
                    
                    # If no active location exists, create one with default values
                    self.logger.info(f"Creating default location for user {user_id}")
                    
                    try:
                        # Create new location
                        location = Location(
                            name='Cincinnati',
                            latitude=39.1031,
                            longitude=-84.5120,
                            radius=25,
                            is_active=True,
                            user_id=user_id
                        )
                        db.session.add(location)
                        db.session.flush()  # Get the ID for the new location
                        
                        # Create new preferences if they don't exist
                        if not prefs:
                            prefs = UserPreferences(user_id=user_id)
                            db.session.add(prefs)
                        
                        # Set the active location
                        prefs.active_location_id = location.id
                        
                        # Commit all changes
                        db.session.commit()
                        
                        self.logger.info(f"Successfully created default location for user {user_id}")
                        return {
                            'name': location.name,
                            'latitude': location.latitude,
                            'longitude': location.longitude,
                            'radius': location.radius
                        }
                    except Exception as e:
                        self.logger.error(f"Error creating default location: {str(e)}", exc_info=True)
                        db.session.rollback()
                        return None
                        
                except Exception as e:
                    self.logger.error(f"Error getting user-specific location: {str(e)}", exc_info=True)
                    return None
            else:
                # Global location (backward compatibility)
                if hasattr(self, 'active_location'):
                    return self.active_location
                return None
                
        except Exception as e:
            self.logger.error(f"Error in get_active_location: {str(e)}", exc_info=True)
            return None

    def _initialize_claude(self):
        """Initialize Claude with the latest API version"""
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

    def _setup_scheduler(self):
        """Start daily report scheduler"""
        try:
            scheduler = BackgroundScheduler()
            
            # Get schedule from config
            hour = int(self.config['email_schedule']['hour'])
            minute = int(self.config['email_schedule']['minute'])
            day = int(self.config['email_schedule']['day'])
            
            # Add job for weekly reports (Friday mornings)
            scheduler.add_job(
                func=self.send_daily_report,
                trigger=CronTrigger(day_of_week='fri', hour=hour, minute=minute),
                id='weekly_report',
                name='Send weekly bird sighting report',
                replace_existing=True
            )
            
            # Add error listener
            scheduler.add_listener(
                self._handle_job_error,
                EVENT_JOB_ERROR | EVENT_JOB_MISSED
            )
            
            scheduler.start()
            logger.info(f"Started daily report scheduler (runs at {hour:02d}:{minute:02d})")
            self.scheduler = scheduler
            
        except Exception as e:
            logger.error(f"Error starting daily reports: {str(e)}")
            self.scheduler = None

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
            
            # Get all users with newsletter subscriptions
            from models import User, db
            users = User.query.filter_by(newsletter_subscription=True).all()
            
            if not users:
                self.logger.info("No users with newsletter subscriptions found")
                return
            
            self.logger.info(f"Found {len(users)} users with newsletter subscriptions")
            
            for user in users:
                try:
                    # Get recent observations for this user
                    observations = self.get_recent_observations(user_id=user.id)
                    if not observations:
                        self.logger.info(f"No observations to report for user {user.id}")
                        continue
                    
                    # Format observations for display
                    formatted_observations = []
                    for obs in observations:
                        formatted_obs = f"{obs['comName']} ({obs['howMany']}) at {obs['locName']} on {obs['obsDt']}"
                        formatted_observations.append(formatted_obs)
                    formatted_text = "\n".join(formatted_observations)
                    
                    # Get analysis
                    analysis = self.analyze_recent_sightings(observations, user_id=user.id)
                    
                    # Get user's active location
                    active_location = self.get_active_location(user.id)
                    location_name = active_location['name'] if active_location else "your location"
                    
                    # Prepare email content
                    subject = f"Weekly Bird Sighting Report - {datetime.now().strftime('%Y-%m-%d')}"
                    body = f"""Bird Sighting Report for {location_name}

Recent Observations:
{formatted_text}

Analysis:
{analysis}

This report was generated automatically by the Bird Tracker application.
"""
                    
                    # Send email
                    self.send_email(subject, body, recipient=user.email)
                    self.logger.info(f"Weekly report sent successfully to user {user.id}")
                    
                except Exception as e:
                    self.logger.error(f"Error sending weekly report to user {user.id}: {str(e)}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error sending weekly report: {str(e)}")
            raise

    def send_email(self, subject, body, recipient=None):
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
            recipient_email = recipient or self.config.get('email', 'recipient_email')

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

    def analyze_recent_sightings(self, observations, user_id=None):
        """Analyze recent bird sightings and generate a report"""
        try:
            # Format observations for display
            formatted_observations = []
            for obs in observations:
                formatted_obs = f"{obs['comName']} ({obs['howMany']}) at {obs['locName']} on {obs['obsDt']}"
                formatted_observations.append(formatted_obs)
            formatted_text = "\n".join(formatted_observations)
            
            # Get the active location for this user
            active_location = self.get_active_location(user_id)
            
            # If Claude is available, get AI analysis
            if self.claude:
                return self._get_ai_analysis(observations, active_location)
            else:
                return self._generate_basic_analysis(observations)
            
        except Exception as e:
            logger.error(f"Error analyzing sightings: {str(e)}")
            return f"Error analyzing sightings: {str(e)}"

    def _get_ai_analysis(self, observations, active_location):
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
            if active_location:
                location_info = f"""Location: {active_location['name']}
                Latitude: {active_location['latitude']}
                Longitude: {active_location['longitude']}
                Search radius: {active_location['radius']} miles
                
                """
            
            prompt = f"""Analyze these bird observations and provide insights. DO NOT include any introductory statements or meta-commentary about the format.

            {location_info}
            {observation_text}
            
            Format your response EXACTLY as follows:
            
            <p>Start directly with the main summary paragraph. No introductory statements.</p>

            <ul style="margin-left: 20px;">
                <li>Unusual or rare species for this location:
                    <ul style="margin-left: 20px;">
                        <li>Species Name (Location)</li>
                        <li>Another Species (Location)</li>
                    </ul>
                </li>
            </ul>

            <ul style="margin-left: 20px;">
                <li>Migratory species observed:
                    <ul style="margin-left: 20px;">
                        <li>Species Name (Location)</li>
                        <li>Another Species (Location)</li>
                    </ul>
                </li>
            </ul>

            <ul style="margin-left: 20px;">
                <li>Summary of Birds of Prey:
                    <ul style="margin-left: 20px;">
                        <li>Species Name (Location)</li>
                        <li>Another Species (Location)</li>
                    </ul>
                </li>
            </ul>
            
            Requirements:
            1. Start the main summary paragraph immediately - no introductory statements
            2. Include TWO blank lines after the main summary paragraph
            3. Include ONE blank line between each bulleted section
            4. Keep the main summary paragraph concise but informative
            5. Focus on the species and locations without dates
            6. Use proper HTML formatting for readability
            7. Ensure each section is visually distinct with proper spacing
            8. DO NOT include any meta-commentary about the format or structure"""

            message = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0.7,
                system="You are an expert ornithologist analyzing bird sighting data. Provide direct analysis without any introductory statements or meta-commentary about the format.",
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

    def chat_with_ai(self, message, user_id=None):
        """Chat with the AI assistant about bird sightings."""
        try:
            if not self.claude:
                self.logger.warning("Claude client not initialized, cannot chat with AI")
                return "Sorry, the AI assistant is not available at the moment."
                
            # Get recent observations to provide context
            observations = self.get_recent_observations(user_id)
            observation_context = ""
            
            # Get the active location for this user
            active_location = self.get_active_location(user_id)
            
            # Include location information
            location_info = ""
            if active_location:
                location_info = f"""Current location: {active_location['name']}
                Latitude: {active_location['latitude']}
                Longitude: {active_location['longitude']}
                Search radius: {active_location['radius']} miles
                
                """
            
            if observations:
                # Format observations for display
                formatted_observations = []
                for obs in observations:
                    formatted_obs = f"{obs['comName']} ({obs['howMany']}) at {obs['locName']} on {obs['obsDt']}"
                    formatted_observations.append(formatted_obs)
                formatted_text = "\n".join(formatted_observations)
                
                observation_context = f"""{location_info}
                Here are recent bird observations in the area:
                {formatted_text}
                
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

    def get_recent_observations(self, user_id=None, days_back=7):
        """Get recent bird observations from eBird API."""
        try:
            if not self.api_key:
                self.logger.error("eBird API key is missing")
                raise ValueError("eBird API key is missing")

            # Get active location for the user
            active_location = self.get_active_location(user_id)
            if not active_location:
                self.logger.error(f"No active location found for user {user_id}")
                raise ValueError("No active location found")

            # Validate location data
            if not all(key in active_location for key in ['latitude', 'longitude', 'radius']):
                self.logger.error(f"Invalid location data: {active_location}")
                raise ValueError("Invalid location data in active location")

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Format dates for eBird API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Construct request URL
            base_url = 'https://api.ebird.org/v2/data/obs/geo/recent'
            params = {
                'lat': active_location['latitude'],
                'lng': active_location['longitude'],
                'dist': active_location['radius'],
                'back': days_back,
                'fmt': 'json'
            }

            # Log the request details
            self.logger.info(f"Making eBird API request with params: {params}")

            # Make request to eBird API
            headers = {'X-eBirdApiToken': self.api_key}
            response = requests.get(base_url, params=params, headers=headers)

            # Log the response status and data
            self.logger.info(f"eBird API response status: {response.status_code}")
            self.logger.info(f"eBird API response data: {response.text[:1000]}")  # Log first 1000 chars to avoid huge logs

            if response.status_code != 200:
                self.logger.error(f"eBird API error: {response.status_code} - {response.text}")
                raise Exception(f"eBird API returned status code {response.status_code}")

            observations = response.json()
            self.logger.info(f"Retrieved {len(observations)} observations from eBird API")

            # Transform observations into our format
            transformed_observations = []
            for obs in observations:
                try:
                    # Log the raw observation data
                    self.logger.debug(f"Raw observation data: {obs}")
                    
                    # Transform the observation data to match the frontend's expected format
                    transformed_obs = {
                        'comName': obs.get('comName', 'Unknown Species'),
                        'locName': obs.get('locName', 'Unknown Location'),
                        'obsDt': obs.get('obsDt', ''),
                        'howMany': obs.get('howMany', 1),
                        'lat': obs.get('lat', active_location['latitude']),
                        'lng': obs.get('lng', active_location['longitude'])
                    }
                    
                    # Log the transformed observation
                    self.logger.debug(f"Transformed observation: {transformed_obs}")
                    
                    # Validate the transformed observation
                    if not all(key in transformed_obs for key in ['comName', 'locName', 'obsDt', 'howMany', 'lat', 'lng']):
                        self.logger.error(f"Missing required fields in transformed observation: {transformed_obs}")
                        continue
                        
                    transformed_observations.append(transformed_obs)
                except Exception as e:
                    self.logger.error(f"Error transforming observation: {e}")
                    continue

            self.logger.info(f"Successfully transformed {len(transformed_observations)} observations")
            return transformed_observations

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Network error in get_recent_observations: {str(e)}")
            raise Exception(f"Failed to fetch observations: {str(e)}")
        except ValueError as e:
            self.logger.error(f"Validation error in get_recent_observations: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error in get_recent_observations: {str(e)}")
            raise Exception(f"Failed to get recent observations: {str(e)}")

    def analyze_sightings(self, user_id: int) -> str:
        """Analyze recent bird sightings using Claude AI."""
        try:
            # Get recent observations
            observations = self.get_recent_observations(user_id)
            if not observations:
                return "No recent observations to analyze."
            
            # Format observations for Claude
            formatted_observations = []
            for obs in observations:
                formatted_obs = {
                    'species': obs['comName'],
                    'count': obs['howMany'],
                    'location': obs['locName'],
                    'date': obs['obsDt']
                }
                formatted_observations.append(formatted_obs)
            
            # Create prompt for Claude
            prompt = f"""Analyze these recent bird sightings and provide insights:
            {json.dumps(formatted_observations, indent=2)}
            
            Please provide:
            1. Notable species observed
            2. Patterns in timing or location
            3. Any interesting behaviors or counts
            4. Recommendations for future birdwatching
            """
            
            # Get analysis from Claude
            response = self.claude.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=1000,
                temperature=0.7,
                system="You are an expert birdwatcher and ornithologist. Provide detailed, scientific analysis of bird sightings.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error analyzing sightings: {str(e)}")
            return f"Error analyzing sightings: {str(e)}" 