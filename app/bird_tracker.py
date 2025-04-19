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
        self.ebird_api_key = self.config.get('ebird', 'api_key')
        self.base_url = 'https://api.ebird.org/v2'
        
    def _load_config(self):
        config = ConfigParser()
        config_path = os.path.join(os.path.dirname(__file__), '..', 'config.ini')
        config.read(config_path)
        return config
        
    def get_observations(self, location, start_date, end_date):
        """Get bird observations for a specific location and date range."""
        try:
            headers = {'X-eBirdApiToken': self.ebird_api_key}
            params = {
                'lat': location.latitude,
                'lng': location.longitude,
                'dist': 25,  # 25km radius
                'back': 7,   # Last 7 days
            }
            
            response = requests.get(
                f'{self.base_url}/data/obs/geo/recent',
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"Error getting observations: {str(e)}")
            return []
            
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