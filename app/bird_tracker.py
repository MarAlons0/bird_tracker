from flask import current_app
import logging
from datetime import datetime, timedelta
import requests
from configparser import ConfigParser
import os

logger = logging.getLogger(__name__)

class BirdSightingTracker:
    def __init__(self, db_instance=None, app=None):
        self.db = db_instance
        self.app = app or current_app
        self.config = self._load_config()
        self.ebird_api_key = os.getenv('EBIRD_API_KEY') or self.config.get('ebird', 'api_key')
        self.base_url = 'https://api.ebird.org/v2'
        self.claude = None
        self._initialize_claude()
        logger.info(f"BirdSightingTracker initialized with API key: {self.ebird_api_key[:4]}...")
        
    def _load_config(self):
        config = ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        config.read(config_path)
        return config
        
    def _initialize_claude(self):
        """Initialize Claude API client."""
        try:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if not api_key:
                logger.error("ANTHROPIC_API_KEY not found in environment variables")
                return
            
            logger.info(f"Found ANTHROPIC_API_KEY: {api_key[:4]}...")
            
            from anthropic import Anthropic
            self.claude = Anthropic(api_key=api_key)
            logger.info("Claude client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Claude client: {e}")
            self.claude = None

    def get_recent_observations(self, user_id=None, days_back=7):
        """Get recent bird observations from eBird API or cache."""
        try:
            if not self.ebird_api_key:
                logger.error("eBird API key is missing")
                raise ValueError("eBird API key is missing")

            # Get active location for the user
            active_location = self.get_active_location(user_id)
            if not active_location:
                logger.error(f"No active location found for user {user_id}")
                raise ValueError("No active location found")

            # Validate location data
            if not all(key in active_location for key in ['latitude', 'longitude', 'radius']):
                logger.error(f"Invalid location data: {active_location}")
                raise ValueError("Invalid location data in active location")

            # Check cache first
            from app.models import BirdSightingCache, Location
            location = Location.query.filter_by(
                latitude=active_location['latitude'],
                longitude=active_location['longitude']
            ).first()
            
            if location:
                cache = BirdSightingCache.get_valid_cache(user_id, location.id)
                if cache:
                    logger.info(f"Using cached observations for user {user_id} and location {location.id}")
                    return cache.observations

            # If no valid cache, fetch from eBird API
            logger.info("No valid cache found, fetching from eBird API")
            
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
            logger.info(f"Making eBird API request with params: {params}")

            # Make request to eBird API
            headers = {'X-eBirdApiToken': self.ebird_api_key}
            response = requests.get(base_url, params=params, headers=headers)

            # Log the response status and data
            logger.info(f"eBird API response status: {response.status_code}")
            logger.info(f"eBird API response data: {response.text[:1000]}")  # Log first 1000 chars to avoid huge logs

            if response.status_code != 200:
                logger.error(f"eBird API error: {response.status_code} - {response.text}")
                raise Exception(f"eBird API returned status code {response.status_code}")

            observations = response.json()
            logger.info(f"Retrieved {len(observations)} observations from eBird API")

            # Cache the observations
            if location:
                BirdSightingCache.create_cache(
                    user_id=user_id,
                    location_id=location.id,
                    observations=observations,
                    cache_duration=3600  # Cache for 1 hour
                )
                logger.info(f"Cached observations for user {user_id} and location {location.id}")

            return observations

        except Exception as e:
            logger.error(f"Error getting observations: {str(e)}")
            return []

    def get_active_location(self, user_id):
        """Get the active location for a user."""
        try:
            from app.models import UserPreferences, Location
            with self.app.app_context():
                user_pref = UserPreferences.query.filter_by(user_id=user_id).first()
                if not user_pref or not user_pref.active_location_id:
                    # Set default location to Cincinnati, OH
                    default_location = Location.query.filter_by(name='Cincinnati, OH').first()
                    if not default_location:
                        default_location = Location(
                            place_id='ChIJwYPGcU2tQIgR8zFPo6Sl7qk',
                            name='Cincinnati, OH',
                            latitude=39.1031,
                            longitude=-84.5120,
                            radius=25
                        )
                        self.db.session.add(default_location)
                        self.db.session.commit()
                    user_pref = UserPreferences(user_id=user_id, active_location_id=default_location.id)
                    self.db.session.add(user_pref)
                    self.db.session.commit()
                location = Location.query.get(user_pref.active_location_id)
                return {
                    'latitude': location.latitude,
                    'longitude': location.longitude,
                    'radius': location.radius
                }
        except Exception as e:
            logger.error(f"Error getting active location: {str(e)}")
            return None

    def generate_analysis(self, observations):
        """Generate analysis of bird observations."""
        try:
            # Group observations by species
            species_counts = {}
            for obs in observations:
                species = obs.get('comName')
                if species:
                    species_counts[species] = species_counts.get(species, 0) + 1
            
            # Sort by count
            sorted_species = sorted(species_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                'total_species': len(species_counts),
                'total_observations': len(observations),
                'top_species': sorted_species[:10],
                'observation_dates': list(set(obs.get('obsDt') for obs in observations))
            }
            
        except Exception as e:
            logger.error(f"Error generating analysis: {str(e)}")
            return {}
            
    def create_email_template(self, user, observations, analysis):
        """Create HTML email template for the report."""
        try:
            template = f"""
            <html>
                <body>
                    <h2>Weekly Bird Sighting Report</h2>
                    <p>Hello {user.email},</p>
                    <p>Here's your weekly bird sighting report for {user.default_location}:</p>
                    
                    <h3>Summary</h3>
                    <ul>
                        <li>Total Species Observed: {analysis.get('total_species', 0)}</li>
                        <li>Total Observations: {analysis.get('total_observations', 0)}</li>
                    </ul>
                    
                    <h3>Top Species</h3>
                    <ul>
                        {''.join(f'<li>{species}: {count} sightings</li>' for species, count in analysis.get('top_species', []))}
                    </ul>
                    
                    <p>Thank you for using Bird Tracker!</p>
                </body>
            </html>
            """
            return template
            
        except Exception as e:
            logger.error(f"Error creating email template: {str(e)}")
            return ""
            
    def send_email(self, to, subject, html):
        """Send email using Flask-Mail."""
        try:
            from flask_mail import Message
            mail = current_app.extensions.get('mail')
            
            msg = Message(
                subject=subject,
                recipients=to,
                html=html
            )
            
            mail.send(msg)
            logger.info(f"Email sent successfully to {to}")
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            raise 

    def analyze_sightings(self, location, timeframe=7):
        """Analyze bird sightings for a specific location and timeframe."""
        try:
            # Get recent observations
            observations = self.get_recent_observations(location, timeframe)
            if not observations:
                return "No observations found for the specified location and timeframe."

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
            return self.get_ai_analysis(formatted_observations, location)
        except Exception as e:
            self.logger.error(f"Error analyzing sightings: {e}")
            return f"Error analyzing sightings: {str(e)}"

    def get_ai_analysis(self, sightings_data, location):
        """Get AI analysis of bird sightings using Claude."""
        try:
            if not self.claude:
                logger.error("Claude client not initialized")
                return None

            logger.info(f"Preparing to analyze {len(sightings_data)} sightings for location: {location}")
            
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

            logger.info("Sending request to Claude API...")
            
            prompt = f"""You are an expert Naturalist analyzing bird sighting data for {location}. Analyze these observations and provide insights.

{observation_text}

Format your response EXACTLY as follows:

<p>Start with a comprehensive summary paragraph that covers the overall bird activity in the area, including any notable patterns, unusual sightings, and migration activity. Consider the location and time of year in your analysis.</p>

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
8. Consider the location and time of year in your analysis
9. Highlight any unusual or rare sightings
10. DO NOT include any meta-commentary about the format or structure"""

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

            logger.info("Received response from Claude API")
            
            if not response or not response.content:
                logger.error("Empty response from Claude")
                return None

            # Extract the text content from the response
            if hasattr(response, 'content'):
                if isinstance(response.content, list):
                    text_content = ""
                    for block in response.content:
                        if hasattr(block, 'text'):
                            text_content += block.text + "\n"
                    logger.info("Successfully extracted text content from Claude response")
                    return text_content.strip()
                elif hasattr(response.content, 'text'):
                    logger.info("Successfully extracted text content from Claude response")
                    return response.content.text
                elif isinstance(response.content, str):
                    logger.info("Successfully extracted text content from Claude response")
                    return response.content
                else:
                    logger.error("Unexpected response content type")
                    return str(response.content)
            else:
                logger.error("Response has no content attribute")
                return "Sorry, I couldn't generate a response."

        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}", exc_info=True)
            return None 

    def get_recent_observations_by_location(self, lat, lng, radius, days_back=7):
        """Get recent bird observations from eBird API for a specific location."""
        try:
            if not self.ebird_api_key:
                logger.error("eBird API key is missing")
                raise ValueError("eBird API key is missing")

            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)

            # Format dates for eBird API
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')

            # Construct request URL
            base_url = 'https://api.ebird.org/v2/data/obs/geo/recent'
            params = {
                'lat': lat,
                'lng': lng,
                'dist': radius,
                'back': days_back,
                'fmt': 'json'
            }

            # Log the request details
            logger.info(f"Making eBird API request with params: {params}")

            # Make request to eBird API
            headers = {'X-eBirdApiToken': self.ebird_api_key}
            response = requests.get(base_url, params=params, headers=headers)

            # Log the response status and data
            logger.info(f"eBird API response status: {response.status_code}")
            logger.info(f"eBird API response data: {response.text[:1000]}")  # Log first 1000 chars to avoid huge logs

            if response.status_code != 200:
                logger.error(f"eBird API error: {response.status_code} - {response.text}")
                raise Exception(f"eBird API returned status code {response.status_code}")

            observations = response.json()
            logger.info(f"Retrieved {len(observations)} observations from eBird API")

            return observations

        except Exception as e:
            logger.error(f"Error getting observations: {str(e)}")
            return [] 