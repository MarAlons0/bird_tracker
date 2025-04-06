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
        # Get active carousel images
        carousel_images = db.session.execute(text('''
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
        ''')).fetchall()
        
        # Convert Row objects to dictionaries
        carousel_images = [{
            'id': img.image_id,
            'filename': img.image_url,
            'title': img.image_title,
            'description': img.image_description,
            'order': img.image_order,
            'is_active': img.image_active
        } for img in carousel_images]
        
        logger.info(f"Found {len(carousel_images)} active carousel images")
        for img in carousel_images:
            logger.debug(f"Carousel image: id={img['id']}, title={img['title']}, url={img['filename']}")
        
        # Get current location
        location = db.session.execute(text('''
            SELECT name, latitude, longitude, radius
            FROM locations
            WHERE is_active = true
            ORDER BY id DESC
            LIMIT 1
        ''')).fetchone()
        
        if not location:
            logger.info("No active location found, creating default location")
            # Create default location (Cincinnati)
            db.session.execute(text('''
                INSERT INTO locations (name, latitude, longitude, radius, is_active)
                VALUES (:name, :lat, :lng, :radius, true)
            '''), {
                'name': 'Cincinnati, OH',
                'lat': 39.1031,
                'lng': -84.5120,
                'radius': 25
            })
            db.session.commit()
            
            location = db.session.execute(text('''
                SELECT name, latitude, longitude, radius
                FROM locations
                WHERE is_active = true
                ORDER BY id DESC
                LIMIT 1
            ''')).fetchone()
        
        # Convert location Row to dictionary
        location_dict = {
            'name': location.name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'radius': location.radius
        }
        
        logger.info(f"Current location: {location_dict['name']} ({location_dict['latitude']}, {location_dict['longitude']})")
        
        # Get Google Places API key
        google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not google_places_key:
            logger.error("Google Places API key not found!")
            return render_template('error.html', error="Google Places API key not configured")
        
        return render_template('home.html', 
                           carousel_images=carousel_images,
                           location=location_dict,
                           google_maps_api_key=google_places_key)
                           
    except Exception as e:
        logger.error(f"Error in index route: {str(e)}", exc_info=True)
        return render_template('error.html', error=str(e))

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
        logger.info(f"Received location update request: {data}")
        
        if not data or 'name' not in data:
            return jsonify({'error': 'Location name is required'}), 400
            
        name = data['name']
        radius = data.get('radius', 25)  # Default to 25 miles if not specified
        
        # Check if we have coordinates from the frontend
        if 'latitude' in data and 'longitude' in data:
            lat = float(data['latitude'])
            lng = float(data['longitude'])
            logger.info(f"Using provided coordinates: {lat}, {lng}")
        else:
            # Fall back to predefined cities
            city_coords = {
                'cincinnati': {'lat': 39.1031, 'lng': -84.5120},
                'new york': {'lat': 40.7128, 'lng': -74.0060},
                'los angeles': {'lat': 34.0522, 'lng': -118.2437},
                'chicago': {'lat': 41.8781, 'lng': -87.6298},
                'denver': {'lat': 39.7392, 'lng': -104.9903}
            }
            
            city_key = name.lower()
            if city_key in city_coords:
                coords = city_coords[city_key]
                lat = coords['lat']
                lng = coords['lng']
                logger.info(f"Using predefined city coordinates: {lat}, {lng}")
            else:
                return jsonify({'error': 'Could not find coordinates for this location'}), 400
        
        # Deactivate all current locations
        Location.query.filter_by(active=True).update({'active': False})
        
        # Create new location
        new_location = Location(
            name=name,
            latitude=lat,
            longitude=lng,
            radius=radius,
            active=True
        )
        
        db.session.add(new_location)
        db.session.commit()
        
        logger.info(f"Successfully updated location to: {name} ({lat}, {lng})")
        return jsonify({
            'success': True,
            'location': {
                'name': name,
                'latitude': lat,
                'longitude': lng,
                'radius': radius
            }
        })
        
    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        db.session.rollback()
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