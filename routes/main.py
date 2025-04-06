from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from models import db, User, CarouselImage, Location
from bird_tracker import BirdSightingTracker
import os
import logging
from sqlalchemy import text

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
@login_required
def index():
    """Home page route"""
    try:
        # Get active carousel images with explicit column selection and aliases
        result = db.session.execute(
            text('''
                SELECT 
                    id as image_id,
                    filename as image_url,
                    title as image_title,
                    description as image_description,
                    "order" as image_order,
                    is_active as image_active
                FROM carousel_images 
                WHERE is_active = true 
                ORDER BY "order"
            ''')
        )
        
        # Convert to list of dicts for template
        carousel_images = []
        for row in result:
            try:
                # Access row data using _asdict() method
                row_dict = row._asdict()
                carousel_images.append({
                    'id': row_dict['image_id'],
                    'filename': row_dict['image_url'],
                    'title': row_dict['image_title'],
                    'description': row_dict['image_description'],
                    'order': row_dict['image_order'],
                    'is_active': row_dict['image_active']
                })
            except Exception as row_error:
                print(f"Error processing row: {str(row_error)}")
                print(f"Row data: {row}")
                print(f"Row type: {type(row)}")
                print(f"Row dir: {dir(row)}")
                raise
        
        # Debug logging
        print(f"Found {len(carousel_images)} active carousel images")
        for img in carousel_images:
            print(f"Image ID: {img['id']}")
            print(f"Title: {img['title']}")
            print(f"Filename (Cloudinary URL): {img['filename']}")
            print(f"Is Active: {img['is_active']}")
            print(f"Order: {img['order']}")
            print("---")
        
        # Get active location
        location = None
        if hasattr(current_app, 'tracker') and current_app.tracker.active_location:
            location = current_app.tracker.active_location
        
        # If no location exists, create a default one
        if location is None:
            # Check if there's a location in the database
            location_result = db.session.execute(text('SELECT * FROM locations LIMIT 1')).fetchone()
            
            if location_result:
                # Create a Location object from the database result
                location = Location(
                    id=location_result[0],
                    name=location_result[1],
                    latitude=location_result[2],
                    longitude=location_result[3],
                    radius=location_result[4],
                    is_active=location_result[5]
                )
            else:
                # Create a default location
                location = Location(
                    name="New York City",
                    latitude=40.7128,  # New York City coordinates
                    longitude=-74.0060,
                    radius=25,
                    is_active=True
                )
                db.session.add(location)
                db.session.commit()
                print(f"Created default location: {location.name}")
        
        return render_template('home.html', 
                             carousel_images=carousel_images,
                             location=location)
    except Exception as e:
        print(f"Error in index route: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        # Return empty list of carousel images if there's an error
        return render_template('home.html', 
                             carousel_images=[],
                             location=None)

@bp.route('/map')
@login_required
def map():
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    observations = current_app.tracker.get_recent_observations()
    return render_template('map.html', 
                         observations=observations,
                         location=current_app.tracker.active_location,
                         google_maps_key=google_places_key)

@bp.route('/report')
@login_required
def report():
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    return render_template('report.html',
                         location=current_app.tracker.active_location,
                         google_maps_key=google_places_key)

@bp.route('/api/analysis/basic')
@login_required
def basic_analysis():
    try:
        if not hasattr(current_app, 'tracker'):
            return jsonify({
                'analysis': '<div class="alert alert-warning">Bird tracker is not initialized. Please try again later.</div>'
            })
        
        analysis = current_app.tracker._generate_basic_analysis()
        if not analysis:
            return jsonify({
                'analysis': '<div class="alert alert-info">No recent observations found.</div>'
            })
        
        return jsonify({'analysis': analysis})
    except Exception as e:
        logger.error(f"Error in basic analysis: {e}")
        return jsonify({
            'error': str(e),
            'analysis': '<div class="alert alert-danger">Error generating basic analysis. Please try again later.</div>'
        })

@bp.route('/api/analysis')
@login_required
def ai_analysis():
    try:
        observations = current_app.tracker.get_recent_observations()
        if not observations:
            return jsonify({
                'analysis': 'No recent observations found.'
            })
        
        # Get AI analysis from the tracker
        analysis = current_app.tracker.analyze_recent_sightings(observations)
        
        if not analysis:
            return jsonify({
                'analysis': 'Unable to generate AI analysis.'
            })
        
        # Return the analysis as plain text
        return jsonify({'analysis': analysis})
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        return jsonify({
            'analysis': 'Error generating AI analysis. Please try again later.'
        })

@bp.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        logger.info(f"Processing chat message: {message}")
        response = current_app.tracker.chat_with_ai(message)
        logger.info(f"Chat response received: {response[:100] if response else 'None'}")
        
        if not response:
            logger.warning("No response generated from chat_with_ai")
            return jsonify({
                'error': 'No response generated',
                'response': 'Sorry, I was unable to process your question.'
            }), 500
        
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'response': 'Sorry, there was an error processing your request.'
        }), 500

@bp.route('/api/location', methods=['POST'])
@login_required
def update_location():
    """Update the active location"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Location name is required'}), 400
            
        # Set default values for optional fields
        radius = int(data.get('radius', 25))
        
        # Predefined coordinates for common cities
        city_coordinates = {
            'cincinnati': {'lat': 39.1031, 'lng': -84.5120},
            'denver': {'lat': 39.7392, 'lng': -104.9903},
            'new york': {'lat': 40.7128, 'lng': -74.0060},
            'los angeles': {'lat': 34.0522, 'lng': -118.2437},
            'chicago': {'lat': 41.8781, 'lng': -87.6298},
            'houston': {'lat': 29.7604, 'lng': -95.3698},
            'phoenix': {'lat': 33.4484, 'lng': -112.0740},
            'philadelphia': {'lat': 39.9526, 'lng': -75.1652},
            'san antonio': {'lat': 29.4241, 'lng': -98.4936},
            'san diego': {'lat': 32.7157, 'lng': -117.1611},
            'dallas': {'lat': 32.7767, 'lng': -96.7970},
            'san jose': {'lat': 37.3382, 'lng': -121.8863},
            'austin': {'lat': 30.2672, 'lng': -97.7431},
            'jacksonville': {'lat': 30.3322, 'lng': -81.6557},
            'fort worth': {'lat': 32.7254, 'lng': -97.3208},
            'columbus': {'lat': 39.9612, 'lng': -82.9988},
            'charlotte': {'lat': 35.2271, 'lng': -80.8431},
            'san francisco': {'lat': 37.7749, 'lng': -122.4194},
            'indianapolis': {'lat': 39.7684, 'lng': -86.1581},
            'seattle': {'lat': 47.6062, 'lng': -122.3321}
        }
        
        # Check if the location name contains any of our predefined cities
        location_name = data['name'].lower()
        coordinates = None
        
        for city, coords in city_coordinates.items():
            if city in location_name:
                coordinates = coords
                break
        
        # If no matching city found, use New York City as default
        if not coordinates:
            coordinates = city_coordinates['new york']
        
        # Deactivate all current locations
        db.session.execute(
            text('UPDATE locations SET is_active = false')
        )
        
        # Insert new location
        db.session.execute(
            text('''
                INSERT INTO locations (name, latitude, longitude, radius, is_active)
                VALUES (:name, :lat, :lng, :radius, true)
            '''),
            {
                'name': data['name'],
                'lat': coordinates['lat'],
                'lng': coordinates['lng'],
                'radius': radius
            }
        )
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location updated successfully',
            'location': {
                'name': data['name'],
                'latitude': coordinates['lat'],
                'longitude': coordinates['lng'],
                'radius': radius
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/newsletter-preferences', methods=['GET', 'POST'])
@login_required
def newsletter_preferences():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'toggle':
            current_user.newsletter_subscription = not current_user.newsletter_subscription
            db.session.commit()
            flash(f"Newsletter subscription {'enabled' if current_user.newsletter_subscription else 'disabled'}.", 'success')
            return redirect(url_for('main.newsletter_preferences'))
    
    return render_template('newsletter_preferences.html')

@bp.route('/locations')
@login_required
def locations():
    try:
        # Get all active locations
        locations = Location.query.filter_by(is_active=True).all()
        return render_template('locations.html', locations=locations)
    except Exception as e:
        logger.error(f"Error in locations route: {e}")
        return render_template('error.html', error=str(e))

@bp.route('/sightings')
@login_required
def sightings():
    try:
        # Get recent observations from the tracker
        observations = current_app.tracker.get_recent_observations()
        
        # Get Google Places API key
        google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not google_places_key:
            logger.error("Google Places API key not found!")
            return render_template('error.html', error="Google Places API key not configured")
        
        return render_template('sightings.html',
                             observations=observations,
                             location=current_app.tracker.active_location,
                             google_places_api_key=google_places_key)
    except Exception as e:
        logger.error(f"Error in sightings route: {e}")
        return render_template('error.html', error=str(e))

@bp.route('/profile')
@login_required
def profile():
    try:
        return render_template('profile.html',
                             user=current_user,
                             location=current_app.tracker.active_location)
    except Exception as e:
        logger.error(f"Error in profile route: {e}")
        return render_template('error.html', error=str(e)) 