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
from models import User

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
                logger.warning(f"Location section {location_section} not found in config")
                return None
        except Exception as e:
            logger.error(f"Error getting active location: {str(e)}")
            return None

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
        """Send daily bird sighting report to subscribed users"""
        try:
            # Get all active users
            users = User.query.filter_by(is_active=True).all()
            
            for user in users:
                # Generate report for user's location
                analysis = self.analyze_recent_sightings()
                
                # Send email to user
                self.send_email(analysis, user.email)
                logger.info(f"Daily report sent to {user.email}")
                
        except Exception as e:
            logger.error(f"Error sending daily reports: {str(e)}")
            # Notify admin of failure
            if self.email_config['admin_email']:
                subject = "Bird Tracker Daily Report Error"
                body = f"Failed to send daily reports:\n\n{str(e)}"
                self.send_email(body, self.email_config['admin_email'], subject=subject) 