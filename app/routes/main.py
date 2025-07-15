from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from app.models import db, User, BirdSighting, Location, UserPreferences
from datetime import datetime, timedelta
from app.bird_tracker import BirdSightingTracker
from flask_login import login_required, current_user, login_user, logout_user
from flask import current_app
import os
import logging
from urllib.parse import urlparse
from app.forms import LoginForm
from flask import session

logger = logging.getLogger(__name__)

main = Blueprint('main', __name__)

@main.before_request
def before_request():
    """Log request information for debugging."""
    current_app.logger.info(f"Request path: {request.path}")
    current_app.logger.info(f"User authenticated: {current_user.is_authenticated}")
    current_app.logger.info(f"Session: {session}")
    if current_user.is_authenticated:
        current_app.logger.info(f"Current user: {current_user.username}")

@main.route('/')
@login_required
def home():
    print("GOOGLE_PLACES_API_KEY (route):", current_app.config['GOOGLE_PLACES_API_KEY'])
    try:
        current_app.logger.info(f"Home route accessed by user: {current_user.username if current_user.is_authenticated else 'Not authenticated'}")
        current_app.logger.info(f"User authenticated: {current_user.is_authenticated}")
        current_app.logger.info(f"User active: {current_user.is_active if current_user.is_authenticated else False}")
        # Removed carousel image fetching
        # Get API key and ensure it's not None
        GOOGLE_PLACES_API_KEY = current_app.config.get('GOOGLE_PLACES_API_KEY')
        current_app.logger.info(f"Google Places API Key from config: {GOOGLE_PLACES_API_KEY}")
        if not GOOGLE_PLACES_API_KEY:
            current_app.logger.error("Google Places API Key is not set!")
            GOOGLE_PLACES_API_KEY = ''  # Set empty string instead of None
        # Get user's current location
        user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        location = None
        if user_pref and user_pref.active_location_id:
            location = Location.query.get(user_pref.active_location_id)
        current_app.logger.info(f"Rendering template with API key: {GOOGLE_PLACES_API_KEY}")
        return render_template('home.html', 
                             location=location,
                             GOOGLE_PLACES_API_KEY=GOOGLE_PLACES_API_KEY,
                             config=current_app.config)
    except Exception as e:
        current_app.logger.error(f'Error in home route: {str(e)}')
        return render_template('home.html', 
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
    user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    
    # If no preferences exist or no active location is set, create them with Cincinnati as default
    if not user_pref or not user_pref.active_location_id:
        # Check if Cincinnati location exists
        default_location = Location.query.filter_by(name="Cincinnati, OH").first()
        
        # If Cincinnati doesn't exist, create it
        if not default_location:
            default_location = Location(
                name="Cincinnati, OH",
                latitude=39.1031,
                longitude=-84.512,
                radius=25,  # Default radius of 25 miles
                is_active=True,
                user_id=current_user.id  # Set the user_id to the current user
            )
            db.session.add(default_location)
            db.session.flush()  # Flush to get the location ID
        
        # Create user preferences if they don't exist
        if not user_pref:
            user_pref = UserPreferences(
                user_id=current_user.id,
                active_location_id=default_location.id,
                default_location_id=default_location.id
            )
            db.session.add(user_pref)
        else:
            # Update existing preferences
            user_pref.active_location_id = default_location.id
            user_pref.default_location_id = default_location.id
        
        db.session.commit()
    
    # Get the active location
    active_location = Location.query.get(user_pref.active_location_id)
    
    # Get all locations for the user
    locations = Location.query.filter_by(user_id=current_user.id).all()
    
    return render_template('map.html', 
                         active_location=active_location,
                         locations=locations)

@main.route('/analysis')
@login_required
def analysis():
    """Render the AI analysis page with chatbot interface."""
    user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
    
    # If no preferences exist or no active location is set, create them with Cincinnati as default
    if not user_pref or not user_pref.active_location_id:
        # Check if Cincinnati location exists
        default_location = Location.query.filter_by(name="Cincinnati, OH").first()
        
        # If Cincinnati doesn't exist, create it
        if not default_location:
            default_location = Location(
                name="Cincinnati, OH",
                latitude=39.1031,
                longitude=-84.512,
                radius=25,  # Default radius of 25 miles
                is_active=True,
                user_id=current_user.id  # Set the user_id to the current user
            )
            db.session.add(default_location)
            db.session.flush()  # Flush to get the location ID
        
        # Create user preferences if they don't exist
        if not user_pref:
            user_pref = UserPreferences(
                user_id=current_user.id,
                active_location_id=default_location.id,
                default_location_id=default_location.id
            )
            db.session.add(user_pref)
        else:
            # Update existing preferences
            user_pref.active_location_id = default_location.id
            user_pref.default_location_id = default_location.id
        
        db.session.commit()
    
    # Get the active location
    active_location = Location.query.get(user_pref.active_location_id)
    
    # Get all locations for the user
    locations = Location.query.filter_by(user_id=current_user.id).all()
    
    return render_template('analysis.html', 
                         active_location=active_location,
                         locations=locations)

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
        # Removed newsletter subscription stats
        # Get recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_users = session.query(User).filter(User.created_at >= week_ago).count()
    return jsonify({
        'total_users': total_users,
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
    bird_name_lower = bird_name.lower()
    
    # Waterbirds
    waterbirds = [
        'duck', 'goose', 'swan', 'loon', 'grebe', 'heron', 'egret', 'crane', 'pelican', 
        'cormorant', 'rail', 'kingfisher', 'gull', 'tern', 'shorebird', 'sandpiper', 
        'plover', 'snipe', 'killdeer', 'phalarope', 'stilt', 'avocet', 'coot', 'gallinule'
    ]
    
    # Raptors
    raptors = [
        'hawk', 'eagle', 'falcon', 'owl', 'vulture', 'kite', 'harrier', 'osprey'
    ]
    
    # Ground Birds
    ground_birds = [
        'quail', 'grouse', 'turkey', 'dove', 'pigeon', 'roadrunner', 'woodcock'
    ]
    
    # Aerial Specialists
    aerial_specialists = [
        'hummingbird', 'swift', 'swallow', 'nighthawk', 'flycatcher', 'phoebe', 'pewee'
    ]
    
    # Tree Specialists
    tree_specialists = [
        'woodpecker', 'sapsucker', 'flicker', 'nuthatch', 'creeper'
    ]
    
    # Check each category
    if any(term in bird_name_lower for term in waterbirds):
        return 'waterbird'
    elif any(term in bird_name_lower for term in raptors):
        return 'raptor'
    elif any(term in bird_name_lower for term in ground_birds):
        return 'ground_bird'
    elif any(term in bird_name_lower for term in aerial_specialists):
        return 'aerial_specialist'
    elif any(term in bird_name_lower for term in tree_specialists):
        return 'tree_specialist'
    else:
        return 'songbird'  # Default category for Passeriformes

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
        current_app.logger.info(f"BirdSightingTracker initialized, Claude client: {tracker.claude is not None}")
        
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
        
        # Extract location name from location_data (could be object or string)
        location_name = location_data.get('name') if isinstance(location_data, dict) else str(location_data)
        
        # Generate analysis
        current_app.logger.info(f"Calling get_ai_analysis with {len(formatted_observations)} observations for location: {location_name}")
        analysis = tracker.get_ai_analysis(formatted_observations, location_name)
        
        current_app.logger.info(f"Analysis result: {analysis[:200] if analysis else 'None'}...")
        
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

        # Validate radius is one of the allowed values
        allowed_radii = [1, 5, 25, 50]
        if radius not in allowed_radii:
            return jsonify({'error': 'Invalid radius. Must be one of: 1, 5, 25, or 50 miles'}), 400

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

@main.route('/api/chat', methods=['POST'])
@login_required
def chat():
    try:
        data = request.get_json()
        message = data.get('message')
        location = data.get('location')  # <-- new
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        current_app.logger.info(f"Processing chat message: {message}")
        
        # Check if observations were provided in the request
        observations = data.get('observations')
        current_app.logger.info(f"Received observations in request: {observations is not None}")
        if observations:
            current_app.logger.info(f"Number of observations provided: {len(observations)}")
        
        if not observations:
            # If no observations provided, fetch recent observations for context
            current_app.logger.info("No observations provided, fetching from eBird")
            tracker = BirdSightingTracker()
            observations = tracker.get_recent_observations(user_id=current_user.id)
            current_app.logger.info(f"Retrieved {len(observations)} observations from eBird")
        
        # Format observations for context
        context = None
        if observations:
            formatted_observations = []
            for obs in observations:
                # Handle both eBird API format and frontend format
                bird_name = obs.get('comName') or obs.get('bird_name')
                location = obs.get('locName') or obs.get('location')
                timestamp = obs.get('obsDt') or obs.get('timestamp')
                how_many = obs.get('howMany') or obs.get('count', 1)
                
                if bird_name and location and timestamp:
                    formatted_obs = f"{bird_name} ({how_many}) at {location} on {timestamp}"
                    formatted_observations.append(formatted_obs)
            
            context = "\n".join(formatted_observations)
            current_app.logger.info(f"Formatted {len(formatted_observations)} observations for context")
        
        # Create tracker instance for chat
        tracker = BirdSightingTracker()
        
        # Use the tracker's chat_with_ai method
        response = tracker.chat_with_ai(message, context)
        current_app.logger.info(f"Received response from chat_with_ai, length: {len(response) if response else 0}")
        
        if not response:
            current_app.logger.warning("No response generated from chat_with_ai")
            return jsonify({
                'error': 'No response generated',
                'response': 'I apologize, but I was unable to process your question. Please try again.'
            }), 500
        
        return jsonify({'response': response})

    except Exception as e:
        current_app.logger.error(f"Chat error: {str(e)}")
        current_app.logger.error(f"Error type: {type(e)}")
        import traceback
        current_app.logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'response': 'I apologize, but I encountered an error while processing your question. Please try again later.'
        }), 500 