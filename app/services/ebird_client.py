"""eBird API client for fetching bird observation data."""
import logging
import os
from datetime import datetime, timedelta
import requests

logger = logging.getLogger(__name__)


class EBirdClient:
    """Client for interacting with the eBird API."""

    BASE_URL = 'https://api.ebird.org/v2'

    def __init__(self, api_key=None):
        """
        Initialize the eBird client.

        Args:
            api_key: eBird API key. If not provided, reads from EBIRD_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('EBIRD_API_KEY')
        if not self.api_key:
            logger.warning("eBird API key not provided")

    def get_recent_observations(self, lat, lng, radius, days_back=7):
        """
        Get recent bird observations from eBird API for a specific location.

        Args:
            lat: Latitude of the center point
            lng: Longitude of the center point
            radius: Search radius in kilometers (max 50)
            days_back: Number of days to look back (max 30)

        Returns:
            List of observation dictionaries from eBird API
        """
        if not self.api_key:
            logger.error("eBird API key is missing")
            return []

        try:
            url = f'{self.BASE_URL}/data/obs/geo/recent'
            params = {
                'lat': lat,
                'lng': lng,
                'dist': min(radius, 50),  # Max 50km
                'back': min(days_back, 30),  # Max 30 days
                'fmt': 'json'
            }

            headers = {'X-eBirdApiToken': self.api_key}

            logger.info(f"Fetching eBird data: lat={lat}, lng={lng}, radius={radius}")
            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"eBird API error: {response.status_code} - {response.text[:500]}")
                return []

            observations = response.json()
            logger.info(f"Retrieved {len(observations)} observations from eBird")
            return observations

        except requests.exceptions.Timeout:
            logger.error("eBird API request timed out")
            return []
        except requests.exceptions.RequestException as e:
            logger.error(f"eBird API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Error fetching eBird observations: {e}")
            return []

    def get_notable_observations(self, region_code, days_back=7):
        """
        Get notable/rare bird observations for a region.

        Args:
            region_code: eBird region code (e.g., 'US-OH' for Ohio)
            days_back: Number of days to look back

        Returns:
            List of notable observation dictionaries
        """
        if not self.api_key:
            logger.error("eBird API key is missing")
            return []

        try:
            url = f'{self.BASE_URL}/data/obs/{region_code}/recent/notable'
            params = {
                'back': min(days_back, 30),
                'fmt': 'json'
            }

            headers = {'X-eBirdApiToken': self.api_key}
            response = requests.get(url, params=params, headers=headers, timeout=30)

            if response.status_code != 200:
                logger.error(f"eBird API error: {response.status_code}")
                return []

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching notable observations: {e}")
            return []

    def get_species_list(self, region_code):
        """
        Get list of species observed in a region.

        Args:
            region_code: eBird region code

        Returns:
            List of species codes
        """
        if not self.api_key:
            return []

        try:
            url = f'{self.BASE_URL}/product/spplist/{region_code}'
            headers = {'X-eBirdApiToken': self.api_key}
            response = requests.get(url, headers=headers, timeout=30)

            if response.status_code != 200:
                return []

            return response.json()

        except Exception as e:
            logger.error(f"Error fetching species list: {e}")
            return []


# Singleton instance for convenience
_client = None


def get_client():
    """Get or create a singleton eBird client instance."""
    global _client
    if _client is None:
        _client = EBirdClient()
    return _client
