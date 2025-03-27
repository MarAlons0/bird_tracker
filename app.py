from flask import Flask, render_template, jsonify, request, url_for
from flask_cors import CORS
from datetime import datetime
import sys
import os
import json
import logging
from dotenv import load_dotenv
from logging_config import setup_logging
import anthropic

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import bird_tracker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bird_tracker import BirdSightingTracker

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize bird tracker
try:
    tracker = BirdSightingTracker()
    logger.info("Bird tracker initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize bird tracker: {e}")
    raise

def load_locations():
    try:
        with open('locations.json', 'r') as f:
            return json.load(f)
    except TimeoutError:
        print("Timeout while reading locations.json")
        return []
    except FileNotFoundError:
        print("locations.json not found")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in locations.json")
        return []
    except Exception as e:
        print(f"Error loading locations: {e}")
        return []

def get_carousel_images():
    image_dir = os.path.join('static', 'images', 'birds')
    print(f"Looking for images in: {image_dir}")
    images = []
    if os.path.exists(image_dir):
        for file in os.listdir(image_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append(file)
        print(f"Found images: {images}")
    else:
        print(f"Directory not found: {image_dir}")
    return sorted(images)

@app.route('/')
def home():
    try:
        email_schedule = {
            'hour': int(os.getenv('EMAIL_SCHEDULE_HOUR', '7')),
            'minute': int(os.getenv('EMAIL_SCHEDULE_MINUTE', '0'))
        }
        carousel_images = get_carousel_images()
        google_key = os.getenv('GOOGLE_PLACES_API_KEY')
        ebird_key = os.getenv('EBIRD_API_KEY')
        
        if not google_key:
            logger.error("Google Places API key not found!")
            google_key = ''  # Set empty string instead of None

        if not ebird_key:
            logger.error("eBird API key not found!")
            return render_template('error.html', error="eBird API key not configured")
        
        observations = tracker.get_recent_observations()
        logger.debug(f"Found {len(observations)} recent observations")
        
        return render_template('index.html', 
                             location=tracker.active_location,
                             email_schedule=email_schedule,
                             carousel_images=carousel_images,
                             google_maps_key=google_key)
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return render_template('error.html', error=str(e))

@app.route('/map')
def map():
    observations = tracker.get_recent_observations()
    return render_template('map.html', 
                         observations=observations,
                         location=tracker.active_location,
                         google_maps_key=os.getenv('GOOGLE_PLACES_API_KEY'))

@app.route('/report')
def report():
    return render_template('report.html',
                         location=tracker.active_location,
                         google_maps_key=os.getenv('GOOGLE_PLACES_API_KEY'))

@app.route('/api/observations')
def get_observations():
    observations = tracker.get_recent_observations()
    return jsonify(observations)

@app.route('/api/analysis')
def get_analysis():
    try:
        observations = tracker.get_recent_observations()
        logger.debug(f"Analyzing {len(observations)} observations")
        if not observations:
            return jsonify({
                'analysis': '<p class="alert alert-info">No bird sightings found in the last 21 days for this location.</p>'
            })
        
        try:
            analysis = tracker.analyze_observations(observations)
            logger.debug(f"Analysis received, length: {len(analysis) if analysis else 0}")
            if not analysis:
                return jsonify({
                    'analysis': '<p class="alert alert-warning">Unable to generate analysis at this time.</p>'
                })
            
            # Verify the response is valid HTML
            if not analysis.strip().startswith('<'):
                analysis = f"<p>{analysis}</p>"
            
            return jsonify({'analysis': analysis})
        except Exception as analysis_error:
            logger.error(f"Analysis generation error: {analysis_error}")
            return jsonify({
                'error': 'Unable to generate analysis at this time. Please try again later.'
            }), 503
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        error_msg = f"Error during analysis: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/analysis/basic')
def get_basic_analysis():
    try:
        observations = tracker.get_recent_observations()
        if not observations:
            return jsonify({
                'analysis': '<p class="alert alert-info">No bird sightings found in the last 21 days for this location.</p>'
            })
        
        basic_analysis = tracker._generate_basic_analysis(observations, {})
        return jsonify({'analysis': basic_analysis})
        
    except Exception as e:
        logger.error(f"Basic analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/location', methods=['POST'])
def update_location():
    try:
        name = request.form.get('name')
        lat = float(request.form.get('lat'))
        lng = float(request.form.get('lng'))
        radius = int(request.form.get('radius'))
        
        # Validate inputs
        if not all([name, lat, lng, radius]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({"error": "Invalid coordinates"}), 400
        
        if not (1 <= radius <= 50):
            return jsonify({"error": "Radius must be between 1 and 50 miles"}), 400

        # Update tracker location
        tracker.set_location(name, lat, lng, radius)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        # Get current observations and analysis for context
        observations = tracker.get_recent_observations()
        
        # Create prompt with context
        prompt = f"""You are a helpful bird expert assistant. Use the following context to answer the user's question:

Current Location: {tracker.active_location['name']}
Recent Observations: {len(observations)} birds observed
Observation Period: Last 21 days

The user asks: {message}

Please provide a concise, informative response focusing on the bird-related aspects of the question.
"""

        # Get response from Claude
        response = tracker.claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        return jsonify({
            'response': response.content[0].text
        })

    except Exception as e:
        print(f"Chat error: {str(e)}")
        return jsonify({
            'error': 'Error processing chat request'
        }), 500

@app.route('/api/email-schedule', methods=['POST'])
def update_email_schedule():
    try:
        hour = request.form.get('hour')
        minute = request.form.get('minute')
        
        if not all([hour, minute]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = tracker.update_email_schedule(hour, minute)
        if success:
            return jsonify({
                "success": True,
                "message": f"Email schedule updated to {hour:02d}:{minute:02d}"
            })
        else:
            return jsonify({
                "error": "Failed to update email schedule"
            }), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Add error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(host='localhost', port=8000, debug=True) 