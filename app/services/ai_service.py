"""AI service for bird sighting analysis using Claude."""
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI-powered bird sighting analysis using Anthropic's Claude."""

    # Default models
    ANALYSIS_MODEL = "claude-sonnet-4-20250514"
    CHAT_MODEL = "claude-sonnet-4-20250514"

    def __init__(self, api_key=None):
        """
        Initialize the AI service.

        Args:
            api_key: Anthropic API key. If not provided, reads from ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        self.client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Anthropic client."""
        if not self.api_key:
            logger.warning("Anthropic API key not provided")
            return

        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=self.api_key)
            logger.info("Claude client initialized successfully")
        except ImportError:
            logger.error("anthropic package not installed")
        except Exception as e:
            logger.error(f"Error initializing Claude client: {e}")
            self.client = None

    @property
    def is_available(self):
        """Check if the AI service is available."""
        return self.client is not None

    def analyze_observations(self, observations, location_name):
        """
        Generate AI analysis of bird observations.

        Args:
            observations: List of observation dicts with keys: species, count, location, timestamp
            location_name: Name of the location being analyzed

        Returns:
            HTML-formatted analysis string, or None on error
        """
        if not self.client:
            logger.error("Claude client not initialized")
            return None

        try:
            # Format observations for the prompt
            formatted = self._format_observations(observations)

            prompt = self._build_analysis_prompt(formatted, location_name)

            response = self.client.messages.create(
                model=self.ANALYSIS_MODEL,
                max_tokens=4000,
                temperature=0.7,
                system="You are an expert ornithologist analyzing bird sighting data. Provide direct analysis without any introductory statements or meta-commentary about the format.",
                messages=[{"role": "user", "content": prompt}]
            )

            return self._extract_response_text(response)

        except Exception as e:
            logger.error(f"Error getting AI analysis: {e}", exc_info=True)
            return None

    def chat(self, message, context=None):
        """
        Chat with the AI about bird sightings.

        Args:
            message: User's message/question
            context: Optional context about recent sightings

        Returns:
            AI response string, or None on error
        """
        if not self.client:
            logger.error("Claude client not initialized")
            return None

        try:
            prompt = f"""You are an expert ornithologist assistant. Answer questions about bird sightings and bird behavior.

Context of recent bird sightings:
{context if context else 'No recent sightings available.'}

User question: {message}

Please provide a helpful and informative response based on the context and your expertise."""

            response = self.client.messages.create(
                model=self.CHAT_MODEL,
                max_tokens=1000,
                temperature=0.7,
                system="You are an expert ornithologist assistant. Provide accurate and helpful information about birds and bird sightings.",
                messages=[{"role": "user", "content": prompt}]
            )

            return self._extract_response_text(response)

        except Exception as e:
            logger.error(f"Error in chat: {e}", exc_info=True)
            return None

    def _format_observations(self, observations):
        """Format observations for AI prompt."""
        formatted_lines = []
        for obs in observations:
            species = obs.get('species', 'Unknown')
            count = obs.get('count', 1)
            location = obs.get('location', 'Unknown')
            timestamp = obs.get('timestamp', '')

            line = f"- {species} ({count}) at {location} on {timestamp}"

            if obs.get('weather'):
                line += f" (Weather: {obs['weather']})"
            if obs.get('notes'):
                line += f" (Notes: {obs['notes']})"

            formatted_lines.append(line)

        return "\n".join(formatted_lines)

    def _build_analysis_prompt(self, observation_text, location):
        """Build the analysis prompt for Claude."""
        return f"""You are an expert Naturalist analyzing bird sighting data for {location}. Analyze these observations and provide insights.

{observation_text}

Format your response EXACTLY as follows:

<p>Start with a comprehensive summary paragraph that covers the overall bird activity in the area, including any notable patterns, unusual sightings, and migration activity. Consider the location and time of year in your analysis.</p>

<ul style="margin-left: 20px;">
    <li>Unusual or rare species for this location:
        <ul style="margin-left: 20px;">
            <li>Species Name (Location)</li>
        </ul>
    </li>
</ul>

<ul style="margin-left: 20px;">
    <li>Migratory species observed:
        <ul style="margin-left: 20px;">
            <li>Species Name (Location)</li>
        </ul>
    </li>
</ul>

<ul style="margin-left: 20px;">
    <li>Summary of Birds of Prey:
        <ul style="margin-left: 20px;">
            <li>Species Name (Location)</li>
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
7. Consider the location and time of year in your analysis
8. Highlight any unusual or rare sightings
9. DO NOT include any meta-commentary about the format or structure"""

    def _extract_response_text(self, response):
        """Extract text content from Claude response."""
        if not response or not response.content:
            logger.error("Empty response from Claude")
            return None

        if isinstance(response.content, list):
            text_parts = []
            for block in response.content:
                if hasattr(block, 'text'):
                    text_parts.append(block.text)
            return "\n".join(text_parts).strip()
        elif hasattr(response.content, 'text'):
            return response.content.text
        elif isinstance(response.content, str):
            return response.content
        else:
            return str(response.content)


# Singleton instance
_service = None


def get_service():
    """Get or create a singleton AI service instance."""
    global _service
    if _service is None:
        _service = AIService()
    return _service
