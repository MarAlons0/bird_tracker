from flask import Flask, render_template, request, jsonify
from bird_tracker import BirdSightingTracker
import os
from dotenv import load_dotenv

app = Flask(__name__)
load_dotenv()

# Initialize the bird tracker
tracker = BirdSightingTracker()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/update-location', methods=['POST'])
def update_location():
    data = request.json
    try:
        tracker.set_location(
            name=data['name'],
            latitude=float(data['latitude']),
            longitude=float(data['longitude']),
            radius=float(data['radius'])
        )
        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

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