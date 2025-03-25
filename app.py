from flask import Flask, render_template, request, jsonify
from bird_tracker import BirdSightingTracker
import os
from dotenv import load_dotenv
import requests
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
load_dotenv()

# Initialize the bird tracker
tracker = BirdSightingTracker()

@app.route('/')
def index():
    try:
        # Get API key
        api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
        if not api_key:
            logger.error("Google Maps API key not configured")
            return render_template('error.html', 
                               error="Google Maps API key not configured")
      
        # Test each API separately
        api_tests = {}
        
        # Test Geocoding API
        geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Cincinnati&key={api_key}"
        try:
            response = requests.get(geocode_url)
            api_tests['geocoding'] = {
                'status': response.status_code,
                'response': response.json(),
                'headers': dict(response.headers)
            }
            logger.debug("Geocoding API Response: %s", api_tests['geocoding'])
        except Exception as e:
            logger.error("Geocoding API failed: %s", str(e))
            api_tests['geocoding'] = {'error': str(e)}

        # Test Places API
        places_url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input=test&key={api_key}"
        try:
            response = requests.get(places_url)
            api_tests['places'] = {
                'status': response.status_code,
                'response': response.json(),
                'headers': dict(response.headers)
            }
            logger.debug("Places API Response: %s", api_tests['places'])
        except Exception as e:
            logger.error("Places API failed: %s", str(e))
            api_tests['places'] = {'error': str(e)}
        
        return render_template('index.html', 
                           google_maps_api_key=api_key,
                           debug_info={
                               'api_tests': api_tests,
                               'billing_enabled': True
                           })
                           
    except Exception as e:
        logger.error("Error in index route: %s", str(e), exc_info=True)
        return render_template('error.html', 
                           error=f"Server error: {str(e)}")

@app.route('/api/update-location', methods=['POST'])
def update_location():
    data = request.json
    try:
        # Validate input
        required_fields = ['name', 'latitude', 'longitude', 'radius']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400

        # Validate coordinates
        lat = float(data['latitude'])
        lng = float(data['longitude'])
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({
                'status': 'error',
                'message': 'Invalid coordinates'
            }), 400

        # Update location
        tracker.set_location(
            name=data['name'],
            latitude=lat,
            longitude=lng,
            radius=float(data['radius'])
        )
        
        print(f"Location updated to: {data['name']} ({lat}, {lng})")
        return jsonify({'status': 'success'})
    except Exception as e:
        print(f"Error updating location: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    try:
        # Get observations for the specified location
        observations = tracker.get_recent_observations()
        
        # Create a custom prompt based on user query
        prompt = f"""
        Analyze these bird observations with focus on: {data['query']}
        
        Observations:
        {observations}
        
        Please provide specific insights about {data['query']}.
        """
        
        # Get analysis from Claude
        response = tracker.claude.messages.create(
            model="claude-3-opus-20240229",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        
        return jsonify({
            'status': 'success',
            'analysis': response.content[0].text
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True) 