"""Email service for sending bird tracker reports."""
import logging
import os
from urllib.parse import urlencode

import requests
from flask import current_app

from app.services.bird_categories import (
    CATEGORY_PRIORITY, GROUP_COLORS, GROUP_LABELS, categorize,
)

logger = logging.getLogger(__name__)

SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


class EmailService:
    """Service for sending email reports."""

    def __init__(self, mail=None):
        """
        Initialize the email service.

        Args:
            mail: Flask-Mail instance. If not provided, gets from current_app.
        """
        self._mail = mail

    @property
    def mail(self):
        """Get the Flask-Mail instance."""
        if self._mail:
            return self._mail
        return current_app.extensions.get('mail')

    def send(self, to, subject, html, text=None):
        """
        Send an email.

        Prefers the SendGrid HTTP API (works on Render's free tier, where
        outbound SMTP is blocked). Falls back to Flask-Mail/SMTP when SendGrid
        isn't configured — handy for local development.

        Args:
            to: Recipient email address(es) - string or list
            subject: Email subject
            html: HTML body content
            text: Plain text body (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        recipients = [to] if isinstance(to, str) else to

        api_key = os.getenv('SENDGRID_API_KEY')
        from_email = os.getenv('SENDGRID_FROM_EMAIL')
        if api_key and from_email:
            return self._send_via_sendgrid(api_key, from_email, recipients, subject, html, text)

        return self._send_via_smtp(recipients, subject, html, text)

    def _send_via_sendgrid(self, api_key, from_email, recipients, subject, html, text):
        """Send an HTML email through the SendGrid HTTP API."""
        content = []
        if text:
            content.append({'type': 'text/plain', 'value': text})
        content.append({'type': 'text/html', 'value': html})

        payload = {
            'personalizations': [{'to': [{'email': r} for r in recipients]}],
            'from': {'email': from_email, 'name': 'Bird Tracker'},
            'subject': subject,
            'content': content,
        }

        try:
            response = requests.post(
                SENDGRID_URL,
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json',
                },
                json=payload,
                timeout=10,
            )
        except requests.RequestException as e:
            logger.error(f"SendGrid request failed: {e}")
            return False

        if response.status_code in (200, 202):
            logger.info(f"Email sent successfully via SendGrid to {recipients}")
            return True

        logger.error(f"SendGrid error {response.status_code}: {response.text}")
        return False

    def _send_via_smtp(self, recipients, subject, html, text):
        """Send an email through Flask-Mail/SMTP (local-dev fallback)."""
        try:
            from flask_mail import Message

            if not self.mail:
                logger.error("Flask-Mail not configured")
                return False

            msg = Message(
                subject=subject,
                recipients=recipients,
                html=html,
                body=text
            )

            self.mail.send(msg)
            logger.info(f"Email sent successfully via SMTP to {recipients}")
            return True

        except Exception as e:
            logger.error(f"Error sending email via SMTP: {e}")
            return False

    def _build_map_url(self, observations, center):
        """Build a Mapbox static-image URL of the week's sightings.

        Sightings are deduped by location (so a busy hotspot doesn't collapse to
        a single stacked pin), each spot is colored by its most notable group
        (matching the app's palette), and the result is capped at 40 spots to
        stay within Mapbox URL limits.

        Returns (url, present_categories). url is None when no token or center
        point is available, in which case the email omits the map.
        """
        token = os.getenv('MAPBOX_TOKEN')
        if not token or not center:
            return None, set()

        # Group by ~100 m cell; keep the most notable category seen at each spot.
        spots = {}
        for obs in observations:
            lat = obs.get('lat')
            lng = obs.get('lng')
            if lat is None or lng is None:
                continue
            cat = categorize(obs.get('comName') or obs.get('species') or '')
            key = (round(lat, 3), round(lng, 3))
            prev = spots.get(key)
            if prev is None or CATEGORY_PRIORITY.index(cat) < CATEGORY_PRIORITY.index(prev[2]):
                spots[key] = (lat, lng, cat)

        spot_list = list(spots.values())[:40]
        present = {cat for (_, _, cat) in spot_list}

        clat, clng = center
        if spot_list:
            markers = ",".join(
                f"pin-s+{GROUP_COLORS.get(cat, GROUP_COLORS['other'])}({lng},{lat})"
                for (lat, lng, cat) in spot_list
            )
            path = f"{markers}/auto"
        else:
            path = f"{clng},{clat},9"

        url = (f"https://api.mapbox.com/styles/v1/mapbox/streets-v12/static/"
               f"{path}/600x300@2x?access_token={token}")
        return url, present

    def create_weekly_report(self, user, observations, analysis, narrative=None,
                             center=None, location_name=None, radius=None):
        """
        Create HTML email template for the weekly bird report.

        Args:
            user: User object with email attribute
            observations: List of observation data
            analysis: Analysis dict with total_species, total_observations, top_species
            narrative: Optional AI-generated HTML narrative
            notable: Optional list of notable/rare observation dicts
            center: Optional (lat, lng) tuple for the map center
            location_name: Optional location name (looked up if not provided)

        Returns:
            HTML string for the email body
        """
        # Resolve the location name if the caller didn't supply one. (Trip
        # reports pass location_name explicitly and have no User object.)
        if not location_name:
            location_name = "your area"
            if user is not None:
                try:
                    from app.models import UserPreferences, Location
                    user_pref = UserPreferences.query.filter_by(user_id=user.id).first()
                    if user_pref and user_pref.active_location_id:
                        location = Location.query.get(user_pref.active_location_id)
                        if location:
                            location_name = location.name
                except Exception as e:
                    logger.warning(f"Could not get location name: {e}")

        # Absolute base URL — email clients can't resolve relative paths.
        base_url = (os.getenv('APP_BASE_URL') or os.getenv('RENDER_EXTERNAL_URL')
                    or 'https://bird-tracker.onrender.com').rstrip('/')
        manage_url = f"{base_url}/newsletter-preferences"

        # Deep links carry this report's location so the app opens on it rather
        # than the viewer's last-used location (the map/analysis pages read these
        # query params). Omitted when there's no center.
        loc_query = ""
        if center:
            loc_query = "?" + urlencode({
                'lat': center[0],
                'lng': center[1],
                'name': location_name or '',
                'radius': radius or 25,
            })
        map_link = f"{base_url}/{loc_query}"
        analysis_link = f"{base_url}/analysis{loc_query}"

        # Hotspot map (Mapbox static image — fetched by the recipient's client),
        # with a colour legend matching the app's category palette.
        map_url, map_groups = self._build_map_url(observations, center)
        map_html = ""
        if map_url:
            legend_chips = "".join(
                f'<span style="display:inline-block;margin:0 12px 4px 0;font-size:11px;color:#666;">'
                f'<span style="display:inline-block;width:10px;height:10px;border-radius:50%;'
                f'background:#{GROUP_COLORS[cat]};vertical-align:middle;margin-right:5px;"></span>'
                f'{GROUP_LABELS[cat]}</span>'
                for cat in CATEGORY_PRIORITY if cat in map_groups
            )
            map_html = (
                f'<img src="{map_url}" alt="Map of this week\'s sightings" width="600" '
                f'style="width:100%;max-width:600px;border-radius:6px;display:block;margin:8px 0 6px;" />'
                f'<div style="margin:0 0 12px;">{legend_chips}</div>'
            )

        # AI narrative (already HTML; grounds its rare-species list on eBird's
        # notable flags). Omitted if generation failed.
        narrative_html = f'<h3>This week around you</h3>{narrative}' if narrative else ""

        # Most abundant species (ranked by individual birds counted, not records)
        top_species_html = ""
        for species, count in analysis.get('top_species', [])[:5]:
            noun = "bird" if count == 1 else "birds"
            top_species_html += f"<li>{species} — {count} {noun}</li>\n"

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                h2 {{ color: #2c5530; }}
                h3 {{ color: #4a7c59; }}
                ul {{ padding-left: 20px; }}
                .btn {{ display:inline-block; padding:10px 18px; margin-right:8px;
                        border-radius:6px; text-decoration:none; font-size:14px; }}
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Weekly Bird Sighting Report</h2>
                <p>Here's your weekly report for <strong>{location_name}</strong>:</p>

                {map_html}

                <h3>Summary</h3>
                <ul>
                    <li>Species observed: <strong>{analysis.get('total_species', 0)}</strong></li>
                    <li>Individual birds counted: <strong>{analysis.get('total_individuals', 0)}</strong></li>
                </ul>

                {narrative_html}

                <h3>Most abundant species</h3>
                <ul>
                    {top_species_html if top_species_html else '<li>No species data available</li>'}
                </ul>

                <p style="margin-top:24px;">
                    <a class="btn" href="{map_link}" style="background:#2c5530;color:#ffffff;">View on map</a>
                    <a class="btn" href="{analysis_link}" style="border:1px solid #2c5530;color:#2c5530;">See full analysis</a>
                </p>

                <div class="footer">
                    <p>Thank you for using Bird Tracker!</p>
                    <p><small>You're receiving this because you subscribed to weekly reports.
                    <a href="{manage_url}">Manage your subscription or unsubscribe</a>.</small></p>
                </div>
            </div>
        </body>
        </html>
        """

    def send_weekly_report(self, user, observations, analysis):
        """
        Send weekly bird report to a user.

        Args:
            user: User object
            observations: List of observations
            analysis: Analysis data dict

        Returns:
            True if sent successfully, False otherwise
        """
        html = self.create_weekly_report(user, observations, analysis)
        return self.send(
            to=user.email,
            subject="Your Weekly Bird Sighting Report",
            html=html
        )


# Singleton instance
_service = None


def get_service():
    """Get or create a singleton email service instance."""
    global _service
    if _service is None:
        _service = EmailService()
    return _service
