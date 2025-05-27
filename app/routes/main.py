from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from app.models import db, User, NewsletterSubscription, BirdSighting, CarouselImage, Location, UserPreferences
from datetime import datetime, timedelta
from app.bird_tracker import BirdSightingTracker
from flask_login import login_required, current_user
from flask import current_app
import os

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def home():
    """Render the home page where users select their location."""
    try:
        # Get active carousel images ordered by their order field
        current_app.logger.info("Fetching carousel images...")
        carousel_images = CarouselImage.query.filter_by(is_active=True).order_by(CarouselImage.order).all()
        current_app.logger.info(f"Found {len(carousel_images)} carousel images")
        
        # Get API key and ensure it's not None
        api_key = current_app.config.get('GOOGLE_PLACES_API_KEY')
        if not api_key:
            current_app.logger.error("Google Places API Key is not set!")
            api_key = ''  # Set empty string instead of None
        
        # Get user's current location
        user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        location = None
        if user_pref and user_pref.active_location_id:
            location = Location.query.get(user_pref.active_location_id)
        
        return render_template('home.html', 
                             carousel_images=carousel_images,
                             location=location,
                             GOOGLE_PLACES_API_KEY=api_key,
                             config=current_app.config)
    except Exception as e:
        current_app.logger.error(f'Error in home route: {str(e)}')
        return render_template('home.html', 
                             carousel_images=[],
                             location=None,
                             GOOGLE_PLACES_API_KEY='',
                             config={})

@main.route('/profile')
@login_required
def profile():
    """Render the user profile page."""
    return render_template('profile.html')

@main.route('/map')
@login_required
def map():
    """Render the map page showing bird observations for the selected location."""
    # Get API key and ensure it's not None
    api_key = current_app.config.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        current_app.logger.error("Google Places API Key is not set!")
        api_key = os.environ.get('GOOGLE_PLACES_API_KEY', '')
    
    if not api_key:
        return render_template('error.html', error="Google Places API key not configured")
    
    # Get user's location from preferences
    user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    if not user_pref or not user_pref.active_location_id:
        return redirect(url_for('main.home'))  # Redirect to home if no location selected
    
    location = Location.query.get(user_pref.active_location_id)
    
    # Get recent observations
    tracker = BirdSightingTracker()
    observations = tracker.get_recent_observations(current_user.id)
    
    return render_template('map.html', 
                         location=location,
                         observations=observations,
                         config=current_app.config)

@main.route('/analysis')
@login_required
def analysis():
    """Render the AI analysis page with chatbot interface."""
    # Get user's location from preferences
    user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    if not user_pref or not user_pref.active_location_id:
        return redirect(url_for('main.home'))  # Redirect to home if no location selected
    
    location = Location.query.get(user_pref.active_location_id)
    
    # Get recent observations for initial analysis
    tracker = BirdSightingTracker()
    observations = tracker.get_recent_observations(current_user.id)
    
    return render_template('analysis.html',
                         location=location,
                         observations=observations,
                         config=current_app.config)

@main.route('/api/status')
@login_required
def status():
    """Return the application status."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@main.route('/api/stats')
@login_required
def stats():
    """Return basic application statistics."""
    with db.session() as session:
        total_users = session.query(User).count()
        active_subscriptions = session.query(NewsletterSubscription).filter_by(is_active=True).count()
        
        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = session.query(User).filter(User.created_at >= week_ago).count()
        
    return jsonify({
        'total_users': total_users,
        'active_subscriptions': active_subscriptions,
        'recent_users': recent_users
    })

@main.route('/api/sightings')
@login_required
def get_sightings():
    """Return recent bird sightings from eBird API."""
    try:
        # Get location parameters from request
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', type=int)
        
        if not all([lat, lng, radius]):
            current_app.logger.error("Missing required location parameters")
            return jsonify([])
            
        current_app.logger.info(f"Fetching sightings for lat: {lat}, lng: {lng}, radius: {radius}")
        
        # Get sightings from eBird API
        tracker = BirdSightingTracker()
        observations = tracker.get_recent_observations_by_location(lat, lng, radius)
        
        # Transform observations to match the frontend's expected format
        sightings = []
        for obs in observations:
            sightings.append({
                'bird_name': obs['comName'],
                'location': obs['locName'],
                'latitude': obs['lat'],
                'longitude': obs['lng'],
                'timestamp': obs['obsDt'],
                'observer': 'eBird User',  # eBird doesn't provide observer names
                'category': get_bird_category(obs['comName'])  # Helper function to categorize birds
            })
        
        return jsonify(sightings)
    except Exception as e:
        current_app.logger.error(f"Error fetching sightings: {e}")
        return jsonify([])

def get_bird_category(bird_name):
    """Helper function to categorize birds for marker colors."""
    # This is a simple categorization - you might want to expand this
    waterfowl = ['duck', 'goose', 'swan', 'grebe', 'coot', 'heron', 'egret', 'crane', 'loon', 'gallinule', 'rail']
    raptor = ['hawk', 'eagle', 'falcon', 'owl', 'vulture', 'osprey', 'kite', 'harrier']
    shorebird = ['sandpiper', 'plover', 'snipe', 'killdeer', 'gull', 'tern', 'shorebird']
    
    bird_name_lower = bird_name.lower()
    
    if any(term in bird_name_lower for term in raptor):
        return 'raptor'
    elif any(term in bird_name_lower for term in waterfowl):
        return 'waterfowl'
    elif any(term in bird_name_lower for term in shorebird):
        return 'shorebird'
    else:
        return 'songbird'  # Default category

@main.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    """Generate AI analysis of bird sightings."""
    try:
        data = request.get_json()
        if not data:
            current_app.logger.error("No JSON data received")
            return jsonify({
                'error': 'No data provided'
            }), 400

        location_data = data.get('location')
        observations = data.get('observations')
        timeframe = int(data.get('timeframe', 7))
        
        if not location_data:
            current_app.logger.error("Location data is required but not provided")
            return jsonify({
                'error': 'Location data is required'
            }), 400
        
        if not observations:
            current_app.logger.error("Observations data is required but not provided")
            return jsonify({
                'error': 'Observations data is required'
            }), 400
        
        current_app.logger.info(f"Generating analysis for location: {location_data}, timeframe: {timeframe} days")
        current_app.logger.info(f"Number of observations: {len(observations)}")
        
        tracker = BirdSightingTracker()
        if not tracker.claude:
            current_app.logger.error("Claude client not initialized")
            return jsonify({
                'error': 'AI service is not available at the moment'
            }), 503
        
        # Format observations for analysis
        formatted_observations = []
        for obs in observations:
            try:
                formatted_obs = {
                    'species': obs.get('species', obs.get('comName', obs.get('bird_name', 'Unknown'))),
                    'count': obs.get('count', obs.get('howMany', 1)),
                    'location': obs.get('location', obs.get('locName', 'Unknown')),
                    'timestamp': obs.get('timestamp', obs.get('obsDt', datetime.utcnow().isoformat())),
                    'weather': obs.get('weather', ''),
                    'notes': obs.get('notes', '')
                }
                formatted_observations.append(formatted_obs)
            except Exception as e:
                current_app.logger.warning(f"Error formatting observation: {str(e)}")
                continue
        
        if not formatted_observations:
            current_app.logger.error("No valid observations after formatting")
            return jsonify({
                'error': 'No valid observations to analyze'
            }), 400
        
        # Generate analysis
        analysis = tracker.get_ai_analysis(formatted_observations, location_data)
        
        if not analysis:
            current_app.logger.error("No analysis generated")
            return jsonify({
                'error': 'Unable to generate analysis'
            }), 500
        
        current_app.logger.info("Analysis generated successfully")
        return jsonify({
            'analysis': analysis
        })
    except Exception as e:
        current_app.logger.error(f"Error in analyze route: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to analyze data'
        }), 500

@main.route('/api/recent-sightings')
@login_required
def recent_sightings():
    """Return recent bird sightings for the home page."""
    with db.session() as session:
        sightings = session.query(BirdSighting).order_by(BirdSighting.timestamp.desc()).limit(10).all()
        return jsonify([{
            'bird_name': sighting.bird_name,
            'location': sighting.location,
            'timestamp': sighting.timestamp.isoformat()
        } for sighting in sightings])

@main.route('/api/carousel-images')
@login_required
def get_carousel_images():
    try:
        # Get active carousel images ordered by their order field
        images = CarouselImage.query.filter_by(is_active=True).order_by(CarouselImage.order).all()
        return jsonify([{
            'id': img.id,
            'url': img.cloudinary_url,  # Use cloudinary_url instead of filename
            'title': img.title,
            'description': img.description
        } for img in images])
    except Exception as e:
        current_app.logger.error(f'Error fetching carousel images: {str(e)}')
        return jsonify({'error': str(e)}), 500

@main.route('/api/update-location', methods=['POST'])
@login_required
def update_location():
    """Update the user's location."""
    try:
        data = request.get_json()
        place_id = data.get('place_id')
        name = data.get('name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 25)  # Default radius of 25 miles

        if not all([place_id, name, latitude, longitude]):
            return jsonify({'error': 'Missing required location data'}), 400

        # Get or create location
        location = Location.query.filter_by(place_id=place_id, user_id=current_user.id).first()
        if not location:
            location = Location(
                place_id=place_id,
                name=name,
                latitude=latitude,
                longitude=longitude,
                radius=radius,
                is_active=True,
                user_id=current_user.id  # Ensure user_id is set
            )
            db.session.add(location)
        else:
            # Update existing location
            location.name = name
            location.latitude = latitude
            location.longitude = longitude
            location.radius = radius
            location.is_active = True

        # Update user preferences
        user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not user_pref:
            user_pref = UserPreferences(user_id=current_user.id)
            db.session.add(user_pref)

        user_pref.active_location_id = location.id
        db.session.commit()

        return jsonify({
            'success': True,
            'location': {
                'name': location.name,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'radius': location.radius
            }
        })
    except Exception as e:
        current_app.logger.error(f'Error updating location: {str(e)}')
        return jsonify({'error': str(e)}), 500

@main.route('/api/user-preferences')
@login_required
def get_user_preferences():
    """Get the user's preferences including current location."""
    try:
        user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not user_pref or not user_pref.active_location_id:
            # Set default location to Cincinnati, OH
            default_location = Location.query.filter_by(name='Cincinnati, OH').first()
            if not default_location:
                default_location = Location(
                    place_id='ChIJwYPGcU2tQIgR8zFPo6Sl7qk',
                    name='Cincinnati, OH',
                    latitude=39.1031,
                    longitude=-84.5120,
                    radius=25
                )
                db.session.add(default_location)
                db.session.commit()
            user_pref = UserPreferences(user_id=current_user.id, active_location_id=default_location.id)
            db.session.add(user_pref)
            db.session.commit()
        location = Location.query.get(user_pref.active_location_id)
        return jsonify({
            'location': {
                'name': location.name,
                'latitude': location.latitude,
                'longitude': location.longitude,
                'radius': location.radius
            }
        })
    except Exception as e:
        current_app.logger.error(f'Error fetching user preferences: {str(e)}')
        return jsonify({'error': str(e)}), 500

@main.route('/api/refresh-sightings', methods=['POST'])
@login_required
def refresh_sightings():
    """Force refresh of bird sightings cache."""
    try:
        # Get the user's location
        user_prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not user_prefs or not user_prefs.active_location:
            return jsonify({
                'error': 'No active location found'
            }), 400

        # Delete existing cache
        from app.models import BirdSightingCache
        BirdSightingCache.query.filter_by(
            user_id=current_user.id,
            location_id=user_prefs.active_location_id
        ).delete()
        db.session.commit()

        # Fetch new data
        tracker = BirdSightingTracker()
        observations = tracker.get_recent_observations(current_user.id)
        
        return jsonify({
            'success': True,
            'message': f'Successfully refreshed {len(observations)} observations'
        })
    except Exception as e:
        current_app.logger.error(f"Error refreshing sightings: {str(e)}")
        return jsonify({
            'error': str(e)
        }), 500 