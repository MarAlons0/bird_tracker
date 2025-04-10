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
                cloudinary_url,
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
            'filename': img.cloudinary_url or img.image_url,  # Use cloudinary_url if available, fallback to filename
            'title': img.image_title,
            'description': img.image_description,
            'order': img.image_order,
            'is_active': img.image_active
        } for img in carousel_images]
        
        logger.info(f"Found {len(carousel_images)} active carousel images")
        for img in carousel_images:
            logger.debug(f"Carousel image: id={img['id']}, title={img['title']}, url={img['filename']}")
        
        # Get current user's location
        location = db.session.execute(text('''
            SELECT l.name, l.latitude, l.longitude, l.radius
            FROM locations l
            JOIN user_preferences up ON up.active_location_id = l.id
            WHERE up.user_id = :user_id AND l.is_active = true
            ORDER BY l.id DESC
            LIMIT 1
        '''), {'user_id': current_user.id}).fetchone()
        
        if not location:
            logger.info("No active location found for user, creating default location")
            # Create default location (Cincinnati) for this user
            db.session.execute(text('''
                INSERT INTO locations (name, latitude, longitude, radius, is_active, user_id)
                VALUES (:name, :lat, :lng, :radius, true, :user_id)
                RETURNING id
            '''), {
                'name': 'Cincinnati, OH',
                'lat': 39.1031,
                'lng': -84.5120,
                'radius': 25,
                'user_id': current_user.id
            })
            
            # Get the new location ID
            new_location_id = db.session.execute(text('''
                SELECT id FROM locations 
                WHERE user_id = :user_id AND is_active = true 
                ORDER BY id DESC LIMIT 1
            '''), {'user_id': current_user.id}).scalar()
            
            # Create or update user preferences
            db.session.execute(text('''
                INSERT INTO user_preferences (user_id, active_location_id)
                VALUES (:user_id, :location_id)
                ON CONFLICT (user_id) 
                DO UPDATE SET active_location_id = :location_id
            '''), {
                'user_id': current_user.id,
                'location_id': new_location_id
            })
            
            db.session.commit()
            
            # Get the newly created location
            location = db.session.execute(text('''
                SELECT name, latitude, longitude, radius
                FROM locations
                WHERE id = :location_id
            '''), {'location_id': new_location_id}).fetchone()
        
        # Convert location Row to dictionary
        location_dict = {
            'name': location.name,
            'latitude': location.latitude,
            'longitude': location.longitude,
            'radius': location.radius
        }
        
        logger.info(f"Current location for user {current_user.id}: {location_dict['name']} ({location_dict['latitude']}, {location_dict['longitude']})")
        
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
        
    observations = current_app.tracker.get_recent_observations(user_id=current_user.id)
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
        observations = current_app.tracker.get_recent_observations(user_id=current_user.id)
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
        
        # Get recent observations for context
        observations = current_app.tracker.get_recent_observations(user_id=current_user.id)
        logger.info(f"Retrieved {len(observations)} observations for context")
        
        # Format observations for context
        context = None
        if observations:
            formatted_observations = []
            for obs in observations:
                formatted_obs = f"{obs['comName']} ({obs['howMany']}) at {obs['locName']} on {obs['obsDt']}"
                formatted_observations.append(formatted_obs)
            context = "\n".join(formatted_observations)
        
        # Use the tracker's chat_with_ai method
        response = current_app.tracker.chat_with_ai(message, context)
        logger.info(f"Received response from chat_with_ai, length: {len(response) if response else 0}")
        
        if not response:
            logger.warning("No response generated from chat_with_ai")
            return jsonify({
                'error': 'No response generated',
                'response': 'I apologize, but I was unable to process your question. Please try again.'
            }), 500
        
        return jsonify({'response': response})

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'response': 'I apologize, but I encountered an error while processing your question. Please try again later.'
        }), 500

@bp.route('/api/location', methods=['POST'])
@login_required
def update_location():
    """Update the user's location"""
    try:
        if not request.is_json:
            current_app.logger.error("Request must be JSON")
            return jsonify({'success': False, 'error': 'Request must be JSON'}), 400

        data = request.get_json()
        current_app.logger.info(f"Received location update request: {data}")

        # Extract location data
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        name = data.get('name')
        radius = data.get('radius', 25)  # Default radius if not provided

        # Validate required fields
        if not all([latitude, longitude, name]):
            current_app.logger.error(f"Missing required location data: {data}")
            return jsonify({'success': False, 'error': 'Missing required location data'}), 400

        try:
            # Update the location
            success = current_app.tracker.set_location(
                user_id=current_user.id,
                name=name,
                lat=float(latitude),
                lng=float(longitude),
                radius=float(radius)
            )

            if not success:
                current_app.logger.error("Failed to update location")
                return jsonify({'success': False, 'error': 'Failed to update location'}), 500

            # Get the updated location
            active_location = current_app.tracker.get_active_location(current_user.id)
            if not active_location:
                current_app.logger.error("Failed to get active location after update")
                return jsonify({'success': False, 'error': 'Failed to get active location'}), 500

            # Get recent observations for the new location
            try:
                observations = current_app.tracker.get_recent_observations(user_id=current_user.id)
                current_app.logger.info(f"Retrieved {len(observations) if observations else 0} observations")
            except Exception as e:
                current_app.logger.error(f"Error getting observations: {str(e)}")
                observations = []

            return jsonify({
                'success': True,
                'location': active_location,
                'observations': observations
            })

        except ValueError as e:
            current_app.logger.error(f"Invalid location data: {str(e)}")
            return jsonify({'success': False, 'error': str(e)}), 400
        except Exception as e:
            current_app.logger.error(f"Error updating location: {str(e)}")
            return jsonify({'success': False, 'error': 'Failed to update location'}), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected error in update_location: {str(e)}")
        return jsonify({'success': False, 'error': 'An unexpected error occurred'}), 500

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
        observations = current_app.tracker.get_recent_observations(user_id=current_user.id)
        
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

@bp.route('/api/observations')
@login_required
def get_observations():
    """Get observations for the current location"""
    try:
        observations = current_app.tracker.get_recent_observations(user_id=current_user.id)
        return jsonify(observations)
    except Exception as e:
        logger.error(f"Error fetching observations: {e}")
        return jsonify({'error': 'Failed to fetch observations'}), 500

@bp.route('/api/ai-analysis')
@login_required
def get_ai_analysis():
    try:
        # Get the user's location
        user_prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not user_prefs or not user_prefs.location:
            return jsonify({
                'status': 'error',
                'message': 'Please set your location in preferences first.'
            }), 400

        # Get recent sightings for the user's location
        recent_sightings = BirdSighting.query.filter_by(
            location_id=user_prefs.location.id
        ).order_by(BirdSighting.timestamp.desc()).limit(10).all()

        if not recent_sightings:
            return jsonify({
                'status': 'error',
                'message': 'No recent bird sightings found for analysis.'
            }), 404

        # Format sightings data for AI analysis
        sightings_data = []
        for sighting in recent_sightings:
            sightings_data.append({
                'species': sighting.species,
                'count': sighting.count,
                'timestamp': sighting.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                'location': sighting.location.name,
                'weather': sighting.weather_conditions,
                'notes': sighting.notes
            })

        # Get AI analysis
        analysis = bird_tracker.get_ai_analysis(sightings_data)
        
        if not analysis:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate AI analysis. Please try again later.'
            }), 500

        return jsonify({
            'status': 'success',
            'analysis': analysis
        })

    except Exception as e:
        app.logger.error(f"Error generating AI analysis: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An unexpected error occurred while generating the analysis.'
        }), 500 