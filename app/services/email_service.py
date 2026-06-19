"""Email service for sending bird tracker reports."""
import logging
import os

import requests
from flask import current_app

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

    def create_weekly_report(self, user, observations, analysis):
        """
        Create HTML email template for weekly bird report.

        Args:
            user: User object with email attribute
            observations: List of observation data
            analysis: Analysis dict with total_species, total_observations, top_species

        Returns:
            HTML string for the email body
        """
        location_name = "your area"

        # Try to get the location name
        try:
            from app.models import UserPreferences, Location
            user_pref = UserPreferences.query.filter_by(user_id=user.id).first()
            if user_pref and user_pref.active_location_id:
                location = Location.query.get(user_pref.active_location_id)
                if location:
                    location_name = location.name
        except Exception as e:
            logger.warning(f"Could not get location name: {e}")

        # Build top species list
        top_species_html = ""
        for species, count in analysis.get('top_species', []):
            top_species_html += f"<li>{species}: {count} sightings</li>\n"

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
                .footer {{ margin-top: 30px; padding-top: 20px; border-top: 1px solid #ddd; font-size: 0.9em; color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h2>Weekly Bird Sighting Report</h2>
                <p>Hello {user.email},</p>
                <p>Here's your weekly bird sighting report for <strong>{location_name}</strong>:</p>

                <h3>Summary</h3>
                <ul>
                    <li>Total Species Observed: <strong>{analysis.get('total_species', 0)}</strong></li>
                    <li>Total Observations: <strong>{analysis.get('total_observations', 0)}</strong></li>
                </ul>

                <h3>Top Species This Week</h3>
                <ul>
                    {top_species_html if top_species_html else '<li>No species data available</li>'}
                </ul>

                <div class="footer">
                    <p>Thank you for using Bird Tracker!</p>
                    <p><small>You're receiving this because you subscribed to weekly reports.</small></p>
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
