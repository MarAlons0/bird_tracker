import requests
from datetime import datetime, timedelta
from configparser import ConfigParser
from collections import defaultdict
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from anthropic import Anthropic
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
import json
import time
import random
import tempfile
from math import cos, sin
from extensions import db
from models import User, Location, UserPreferences
from flask import current_app

# Setup logging
logger = logging.getLogger(__name__)

class BirdSightingTracker:
    def __init__(self, db_instance=None, app=None):
        self.logger = logging.getLogger(__name__)
        self.app = app
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
        
        # Set database instance
        self.db = db_instance or db
        
        # Store the current app context
        if app:
            self.app_context = app.app_context()
        else:
            self.app_context = current_app.app_context() if current_app else None
    
    def __enter__(self):
        """Context manager entry."""
        if self.app_context:
            self.app_context.push()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.app_context:
            self.app_context.pop()
    
    def __del__(self):
        """Cleanup when the BirdSightingTracker instance is destroyed."""
        if hasattr(self, 'app_context') and self.app_context:
            try:
                self.app_context.pop()
            except Exception:
                pass
    
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
        """Initialize the Claude client with API key from environment"""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                self.logger.error("ANTHROPIC_API_KEY not found in environment variables")
                self.claude = None
                return
                
            if not api_key.startswith('sk-ant-'):
                self.logger.error("Invalid ANTHROPIC_API_KEY format")
                self.claude = None
                return
                
            # Initialize the client with just the API key
            self.claude = Anthropic(api_key=api_key)
            self.logger.info("Claude client initialized successfully")
            
            # Test the client with a simple request
            try:
                response = self.claude.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=100,
                    messages=[
                        {"role": "user", "content": "Hello, are you working?"}
                    ]
                )
                self.logger.info(f"Claude API test successful: {response.content[0].text}")
            except Exception as e:
                self.logger.error(f"Claude API test failed: {str(e)}")
                self.claude = None
                
        except Exception as e:
            self.logger.error(f"Error initializing Claude client: {str(e)}", exc_info=True)
            self.claude = None

    def _setup_scheduler(self):
        """Start weekly report scheduler"""
        try:
            if self.scheduler is not None:
                logger.warning("Scheduler already initialized, skipping setup")
                return

            # Check if we're in production environment
            is_production = (
                os.getenv('FLASK_ENV') == 'production' or
                os.getenv('HEROKU_APP_NAME') in ['bird-tracker-app', 'bird-tracker-dev']
            )
            
            if not is_production:
                logger.info("Skipping scheduler setup in non-production environment")
                return

            scheduler = BackgroundScheduler()
            
            # Get schedule from config
            hour = int(self.config['email_schedule']['hour'])
            minute = int(self.config['email_schedule']['minute'])
            day = int(self.config['email_schedule']['day'])
            
            # Convert day number to day name
            day_names = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
            day_name = day_names[day]
            
            # Schedule weekly report email
            scheduler.add_job(
                func=self.send_weekly_report,
                trigger='cron',
                day_of_week=day_name,
                hour=hour,
                minute=minute,
                id='weekly_report',
                replace_existing=True
            )
            
            # Add error listener
            scheduler.add_listener(
                self._handle_job_error,
                EVENT_JOB_ERROR | EVENT_JOB_MISSED
            )
            
            scheduler.start()
            logger.info(f"Started weekly report scheduler (runs on {day_name} at {hour:02d}:{minute:02d})")
            self.scheduler = scheduler
            
        except Exception as e:
            logger.error(f"Error starting weekly reports: {str(e)}")
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

    def send_weekly_report(self):
        """Send weekly report of bird sightings."""
        try:
            self.logger.info("Starting weekly report generation")
            
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
            # Try to get email configuration from environment variables first
            smtp_server = os.getenv('SMTP_SERVER') or self.config.get('email', 'mail_server')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            sender_email = os.getenv('SMTP_USER') or self.config.get('email', 'mail_username')
            sender_password = os.getenv('SMTP_PASSWORD') or self.config.get('email', 'mail_password')
            recipient_email = recipient or os.getenv('RECIPIENT_EMAIL') or self.config.get('email', 'recipient_email')

            # Validate email configuration
            if not all([smtp_server, smtp_port, sender_email, sender_password, recipient_email]):
                self.logger.error("Missing required email configuration")
                raise ValueError("Missing required email configuration")

            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender_email
            msg['To'] = recipient_email

            # Create both plain text and HTML versions
            text = "Please view this email in an HTML-compatible email client."
            html = body

            # Attach both versions
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            msg.attach(part1)
            msg.attach(part2)

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
        """Analyze recent bird sightings and generate a report."""
        try:
            if not observations:
                return "No observations to analyze."
            
            if not self.claude:
                self.logger.warning("Claude client not initialized, cannot analyze sightings")
                return "Unable to generate AI analysis: Claude client not initialized"
            
            # Format observations for AI analysis
            formatted_observations = []
            for obs in observations:
                formatted_obs = {
                    'species': obs['comName'],
                    'count': obs['howMany'],
                    'location': obs['locName'],
                    'timestamp': obs['obsDt'],
                    'weather': obs.get('weather', ''),
                    'notes': obs.get('notes', '')
                }
                formatted_observations.append(formatted_obs)
            
            # Get AI analysis
            self.logger.info("Attempting to get AI analysis...")
            analysis = self.get_ai_analysis(formatted_observations)
            
            if not analysis:
                self.logger.error("AI analysis returned None, falling back to basic analysis")
                return self._generate_basic_analysis(formatted_observations)
            
            self.logger.info("Successfully received AI analysis")
            return analysis
        except Exception as e:
            self.logger.error(f"Error analyzing sightings: {e}", exc_info=True)
            return self._generate_basic_analysis(formatted_observations)

    def get_ai_analysis(self, sightings_data):
        """Get AI analysis of bird sightings."""
        try:
            if not self.claude:
                self.logger.error("Claude client not initialized")
                return None
            
            # Format observations for display
            formatted_observations = []
            for obs in sightings_data:
                observation = f"- {obs['species']} ({obs['count']}) at {obs['location']} on {obs['timestamp']}"
                if obs.get('weather'):
                    observation += f" (Weather: {obs['weather']})"
                if obs.get('notes'):
                    observation += f" (Notes: {obs['notes']})"
                formatted_observations.append(observation)
            observation_text = "\n".join(formatted_observations)
            
            prompt = f"""Analyze these bird observations and provide insights. DO NOT include any introductory statements or meta-commentary about the format.

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
            
            # Get response from Claude
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.7,
                system="You are an expert ornithologist analyzing bird sighting data. Provide direct analysis without any introductory statements or meta-commentary about the format.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            if not response or not response.content:
                self.logger.error("Empty response from Claude")
                return None
            
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
            self.logger.error(f"Error getting AI analysis: {e}", exc_info=True)
            return None

    def _generate_basic_analysis(self, observations):
        """Generate a basic analysis when AI analysis fails."""
        try:
            species_count = {}
            locations = set()
            
            for obs in observations:
                species_count[obs['species']] = species_count.get(obs['species'], 0) + 1
                locations.add(obs['location'])
            
            analysis = "<div class='basic-analysis'>"
            analysis += "<h3>Basic Analysis</h3>"
            
            # Species summary
            analysis += "<h4>Species Observed:</h4>"
            analysis += "<ul>"
            for species, count in species_count.items():
                analysis += f"<li>{species}: {count} observation{'s' if count > 1 else ''}</li>"
            analysis += "</ul>"
            
            # Locations
            analysis += "<h4>Locations:</h4>"
            analysis += "<ul>"
            for location in locations:
                analysis += f"<li>{location}</li>"
            analysis += "</ul>"
            
            analysis += "</div>"
            return analysis
        except Exception as e:
            logger.error(f"Error generating basic analysis: {e}", exc_info=True)
            return "<div class='alert alert-warning'>Unable to generate analysis.</div>"

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
                        'lng': obs.get('lng', active_location['longitude']),
                        'notes': obs.get('notes', '')
                    }
                    
                    # Log the transformed observation
                    self.logger.debug(f"Transformed observation: {transformed_obs}")
                    
                    # Validate the transformed observation
                    if not all(key in transformed_obs for key in ['comName', 'locName', 'obsDt', 'howMany', 'lat', 'lng', 'notes']):
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
            return self.analyze_recent_sightings(observations, user_id)
        except Exception as e:
            logger.error(f"Error analyzing sightings: {str(e)}")
            return f"Error analyzing sightings: {str(e)}"

    def chat_with_ai(self, message: str, context: str = None) -> str:
        """Chat with the AI assistant about bird sightings."""
        try:
            if not self.claude:
                self.logger.error("Claude client not initialized")
                return "I apologize, but I'm not available at the moment. Please try again later."

            # Prepare the system message
            system_message = """You are an expert ornithologist and bird watching assistant. 
            Your role is to help users understand bird sightings, provide information about different species, 
            and answer questions about bird behavior, migration patterns, and identification.
            Be informative but concise, and always maintain a helpful and friendly tone."""

            # Prepare the context and user message
            prompt = message
            if context:
                prompt = f"""Recent bird sightings in your area:
{context}

User question: {message}"""

            # Get response from Claude
            response = self.claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=4000,
                temperature=0.7,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            if not response or not response.content:
                self.logger.error("Empty response from Claude")
                return "I apologize, but I couldn't generate a response. Please try again."

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
                return "I apologize, but I couldn't generate a response. Please try again."

        except Exception as e:
            self.logger.error(f"Error in chat_with_ai: {e}", exc_info=True)
            return "I encountered an error while processing your question. Please try again later." 