from flask import Flask, render_template, request, jsonify
from bird_tracker import BirdSightingTracker
import os
from dotenv import load_dotenv
import requests

app = Flask(__name__)
load_dotenv()

# Initialize the bird tracker
tracker = BirdSightingTracker()

@app.route('/')
def home():
    api_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not api_key:
        return render_template('error.html', 
                             error="Google Maps API key not configured")
    
    # Test with a simpler API endpoint first
    test_url = f"https://maps.googleapis.com/maps/api/geocode/json?address=Cincinnati&key={api_key}"
    try:
        response = requests.get(test_url)
        response_data = response.json()
        print("DEBUG: Geocoding API Test Response:", response_data)
        
        # Now test Places API
        places_url = f"https://maps.googleapis.com/maps/api/place/autocomplete/json?input=test&key={api_key}"
        places_response = requests.get(places_url)
        places_data = places_response.json()
        print("DEBUG: Places API Test Response:", places_data)
        
        return render_template('index.html', 
                             google_maps_api_key=api_key,
                             debug_info={
                                 'geocoding_test': response_data,
                                 'places_test': places_data,
                                 'billing_enabled': True
                             })
            
    except Exception as e:
        print("ERROR: Failed to test APIs:", str(e))
        return render_template('error.html', 
                             error=f"Failed to test APIs: {str(e)}")

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