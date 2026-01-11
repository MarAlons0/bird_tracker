"""
Bird Tracker - Main coordinator class.

This class coordinates between the eBird API, AI analysis, and email services.
For direct access to individual services, import from app.services:
    - EBirdClient: eBird API interactions
    - AIService: Claude AI analysis
    - EmailService: Email sending
"""
from flask import current_app
import logging
from datetime import datetime
from configparser import ConfigParser
import os

from app.services.ebird_client import EBirdClient
from app.services.ai_service import AIService
from app.services.email_service import EmailService

logger = logging.getLogger(__name__)


class BirdSightingTracker:
    """
    Main tracker class that coordinates bird sighting operations.

    This class maintains backward compatibility while delegating to focused services.
    """

    def __init__(self, db_instance=None, app=None):
        """Initialize the tracker with all services."""
        self.db = db_instance
        self.app = app or current_app._get_current_object() if current_app else None

        # Initialize services
        self.ebird = EBirdClient()
        self.ai = AIService()
        self.email = EmailService()

        # Backward compatibility: expose claude client
        self.claude = self.ai.client

        # Legacy config loading
        self.config = self._load_config()
        self.ebird_api_key = self.ebird.api_key
        self.base_url = EBirdClient.BASE_URL

        logger.info(f"BirdSightingTracker initialized")

    def _load_config(self):
        """Load legacy config file if present."""
        config = ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        config.read(config_path)
        return config

    def _initialize_claude(self):
        """Initialize Claude client (backward compatibility)."""
        if not self.ai.client:
            self.ai._initialize_client()
        self.claude = self.ai.client

    # =========================================================================
    # eBird API Methods
    # =========================================================================

    def get_recent_observations(self, user_id=None, days_back=7):
        """Get recent bird observations for a user's active location."""
        try:
            active_location = self.get_active_location(user_id)
            if not active_location:
                logger.error(f"No active location found for user {user_id}")
                return []

            # Check cache first
            from app.models import BirdSightingCache, Location
            location = Location.query.filter_by(
                latitude=active_location['latitude'],
                longitude=active_location['longitude']
            ).first()

            if location:
                cache = BirdSightingCache.get_valid_cache(user_id, location.id)
                if cache:
                    logger.info(f"Using cached observations for user {user_id}")
                    return cache.observations

            # Fetch from eBird
            observations = self.ebird.get_recent_observations(
                lat=active_location['latitude'],
                lng=active_location['longitude'],
                radius=active_location['radius'],
                days_back=days_back
            )

            # Cache the results
            if location and observations:
                BirdSightingCache.create_cache(
                    user_id=user_id,
                    location_id=location.id,
                    observations=observations,
                    cache_duration=3600
                )

            return observations

        except Exception as e:
            logger.error(f"Error getting observations: {e}")
            return []

    def get_recent_observations_by_location(self, lat, lng, radius, days_back=7):
        """Get recent observations for a specific location."""
        return self.ebird.get_recent_observations(lat, lng, radius, days_back)

    def get_active_location(self, user_id):
        """Get the active location for a user."""
        try:
            from app.models import UserPreferences, Location, db

            user_pref = UserPreferences.query.filter_by(user_id=user_id).first()
            if not user_pref or not user_pref.active_location_id:
                # Create default Cincinnati location
                default_location = Location.query.filter_by(name='Cincinnati, OH').first()
                if not default_location:
                    default_location = Location(
                        place_id='ChIJwYPGcU2tQIgR8zFPo6Sl7qk',
                        name='Cincinnati, OH',
                        latitude=39.1031,
                        longitude=-84.5120,
                        radius=25
                    )
                    db.session.add(default_location)
                    db.session.commit()

                if not user_pref:
                    user_pref = UserPreferences(user_id=user_id, active_location_id=default_location.id)
                    db.session.add(user_pref)
                else:
                    user_pref.active_location_id = default_location.id
                db.session.commit()

            location = Location.query.get(user_pref.active_location_id)
            return {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'radius': location.radius
            }
        except Exception as e:
            logger.error(f"Error getting active location: {e}")
            return None

    # =========================================================================
    # AI Analysis Methods
    # =========================================================================

    def get_ai_analysis(self, sightings_data, location):
        """Get AI analysis of bird sightings."""
        return self.ai.analyze_observations(sightings_data, location)

    def chat_with_ai(self, message, context=None):
        """Chat with AI about bird sightings."""
        return self.ai.chat(message, context)

    def analyze_sightings(self, location, timeframe=7):
        """Analyze bird sightings for a location."""
        try:
            observations = self.get_recent_observations(location, timeframe)
            if not observations:
                return "No observations found for the specified location and timeframe."

            formatted = self._format_observations_for_ai(observations)
            return self.ai.analyze_observations(formatted, location)
        except Exception as e:
            logger.error(f"Error analyzing sightings: {e}")
            return f"Error analyzing sightings: {str(e)}"

    def analyze_recent_sightings(self, observations, user_id=None):
        """Analyze recent sightings and generate a report."""
        try:
            if not observations:
                return "No observations to analyze."

            if not self.ai.is_available:
                logger.warning("AI service not available, using basic analysis")
                return self._generate_basic_analysis(observations)

            formatted = self._format_observations_for_ai(observations)
            location = self.get_active_location(user_id)
            location_name = f"{location['latitude']}, {location['longitude']}" if location else "Unknown Location"

            analysis = self.ai.analyze_observations(formatted, location_name)
            return analysis if analysis else self._generate_basic_analysis(observations)

        except Exception as e:
            logger.error(f"Error analyzing sightings: {e}")
            return self._generate_basic_analysis(observations)

    def _format_observations_for_ai(self, observations):
        """Format observations for AI analysis."""
        formatted = []
        for obs in observations:
            if isinstance(obs, dict):
                formatted.append({
                    'species': obs.get('comName', obs.get('bird_name', 'Unknown')),
                    'count': obs.get('howMany', obs.get('count', 1)),
                    'location': obs.get('locName', obs.get('location', 'Unknown')),
                    'timestamp': obs.get('obsDt', obs.get('timestamp', '')),
                    'weather': obs.get('weather', ''),
                    'notes': obs.get('notes', '')
                })
            else:
                # BirdSighting model object
                formatted.append({
                    'species': obs.bird_name,
                    'count': 1,
                    'location': obs.location,
                    'timestamp': obs.timestamp.isoformat() if obs.timestamp else '',
                    'weather': '',
                    'notes': obs.notes or ''
                })
        return formatted

    # =========================================================================
    # Analysis Methods (Non-AI)
    # =========================================================================

    def generate_analysis(self, observations):
        """Generate basic statistical analysis of observations."""
        return self._generate_basic_analysis(observations)

    def _generate_basic_analysis(self, observations):
        """Generate basic analysis without AI."""
        try:
            species_counts = {}
            for obs in observations:
                if isinstance(obs, dict):
                    species = obs.get('comName', obs.get('species', obs.get('bird_name')))
                else:
                    species = obs.bird_name

                if species:
                    species_counts[species] = species_counts.get(species, 0) + 1

            sorted_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)

            return {
                'total_species': len(species_counts),
                'total_observations': len(observations),
                'top_species': sorted_species[:10],
                'observation_dates': list(set(
                    obs.get('obsDt', obs.get('timestamp', '')) if isinstance(obs, dict) else ''
                    for obs in observations
                ))
            }
        except Exception as e:
            logger.error(f"Error generating basic analysis: {e}")
            return {}

    # =========================================================================
    # Email Methods
    # =========================================================================

    def create_email_template(self, user, observations, analysis):
        """Create HTML email template for the report."""
        return self.email.create_weekly_report(user, observations, analysis)

    def send_email(self, to, subject, html):
        """Send email using Flask-Mail."""
        if isinstance(to, str):
            to = [to]
        return self.email.send(to, subject, html)
