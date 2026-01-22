from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from app.models import User, Location, UserPreferences
from config.extensions import db
from app.bird_tracker import BirdSightingTracker
from datetime import datetime
import os
import logging
from sqlalchemy import text

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
@login_required
def home():
    """Home page route"""
    try:
        logger.info("Home route called")
        logger.info(f"Template folder: {current_app.template_folder}")
        logger.info(f"Template files: {os.listdir(current_app.template_folder)}")
        
        # Log the absolute path of the template we're trying to use
        template_path = os.path.join(current_app.template_folder, 'home.html')
        logger.info(f"Attempting to render template at: {template_path}")
        logger.info(f"Template exists: {os.path.exists(template_path)}")
        
        # Log the template loader's search paths
        logger.info("Template loader search paths:")
        if hasattr(current_app.jinja_loader, 'searchpath'):
            # FileSystemLoader has searchpath attribute
            logger.info(f"Search path: {current_app.jinja_loader.searchpath}")
        elif hasattr(current_app.jinja_loader, 'loaders'):
            # ChoiceLoader has loaders attribute
            for loader in current_app.jinja_loader.loaders:
                logger.info(f"Loader: {loader}")
                if hasattr(loader, 'searchpath'):
                    logger.info(f"Search path: {loader.searchpath}")
        else:
            logger.info(f"Loader type: {type(current_app.jinja_loader)}")
        
        google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
        return render_template('home.html', GOOGLE_PLACES_API_KEY=google_places_key)
    except Exception as e:
        logger.error(f"Error in home route: {str(e)}", exc_info=True)
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

        # Use observations from frontend if provided, otherwise fetch new ones
        observations = data.get('observations')
        if observations:
            logger.info(f"Using {len(observations)} observations from frontend")
        else:
            observations = current_app.tracker.get_recent_observations(user_id=current_user.id)
            logger.info(f"Retrieved {len(observations)} observations from API")
        
        # Format observations for context
        context = None
        if observations:
            formatted_observations = []
            for obs in observations:
                formatted_obs = f"{obs.get('comName', 'Unknown')} ({obs.get('howMany', 'X')}) at {obs.get('locName', 'Unknown')} on {obs.get('obsDt', '')}"
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

@bp.route('/api/sightings')
@login_required
def get_sightings():
    """Return recent bird sightings from eBird API with location parameters."""
    try:
        # Get location parameters from request
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', type=int)
        
        if not all([lat, lng, radius]):
            logger.error("Missing required location parameters")
            return jsonify([])
            
        logger.info(f"Fetching sightings for lat: {lat}, lng: {lng}, radius: {radius}")
        
        # Get sightings from eBird API using the tracker
        tracker = current_app.tracker
        observations = tracker.get_recent_observations_by_location(lat, lng, radius)
        
        # Transform observations to match the frontend's expected format
        sightings = []
        for obs in observations:
            sightings.append({
                'bird_name': obs.get('comName', obs.get('bird_name', 'Unknown')),
                'location': obs.get('locName', obs.get('location', 'Unknown')),
                'latitude': obs.get('lat', obs.get('latitude', 0)),
                'longitude': obs.get('lng', obs.get('longitude', 0)),
                'timestamp': obs.get('obsDt', obs.get('timestamp', '')),
                'observer': obs.get('observer', 'eBird User'),
                'category': _get_bird_category(obs.get('comName', obs.get('bird_name', '')))
            })
        
        return jsonify(sightings)
    except Exception as e:
        logger.error(f"Error fetching sightings: {e}", exc_info=True)
        return jsonify([])

def _get_bird_category(bird_name):
    """Helper function to categorize birds for marker colors."""
    if not bird_name:
        return 'songbird'
    
    bird_name_lower = bird_name.lower()
    
    # Waterfowl
    waterfowl_keywords = ['duck', 'goose', 'swan', 'teal', 'wigeon', 'pintail', 'shoveler', 'gadwall', 'mallard']
    if any(keyword in bird_name_lower for keyword in waterfowl_keywords):
        return 'waterfowl'
    
    # Raptors
    raptor_keywords = ['hawk', 'eagle', 'falcon', 'owl', 'osprey', 'vulture', 'kite', 'harrier']
    if any(keyword in bird_name_lower for keyword in raptor_keywords):
        return 'raptor'
    
    # Shorebirds
    shorebird_keywords = ['sandpiper', 'plover', 'curlew', 'godwit', 'dunlin', 'killdeer', 'snipe', 'stilt', 'avocet']
    if any(keyword in bird_name_lower for keyword in shorebird_keywords):
        return 'shorebird'
    
    # Default to songbird
    return 'songbird'

@bp.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    """Generate AI analysis of bird sightings."""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({
                'error': 'No data provided'
            }), 400

        location_data = data.get('location')
        observations = data.get('observations')
        timeframe = int(data.get('timeframe', 7))
        
        if not location_data:
            logger.error("Location data is required but not provided")
            return jsonify({
                'error': 'Location data is required'
            }), 400
        
        if not observations:
            logger.error("Observations data is required but not provided")
            return jsonify({
                'error': 'Observations data is required'
            }), 400
        
        logger.info(f"Generating analysis for location: {location_data}, timeframe: {timeframe} days")
        logger.info(f"Number of observations: {len(observations)}")
        
        tracker = current_app.tracker
        logger.info(f"BirdSightingTracker initialized, Claude client: {tracker.claude is not None}")
        
        if not tracker.claude:
            logger.error("Claude client not initialized")
            return jsonify({
                'error': 'AI service is not available at the moment'
            }), 503
        
        # Format observations for analysis
        formatted_observations = []
        for obs in observations:
            try:
                # Handle different observation formats from different endpoints
                species = obs.get('species') or obs.get('comName') or obs.get('bird_name') or 'Unknown'
                count = obs.get('count') or obs.get('howMany') or 1
                location = obs.get('location') or obs.get('locName') or 'Unknown'
                timestamp = obs.get('timestamp') or obs.get('obsDt') or datetime.utcnow().isoformat()
                weather = obs.get('weather') or obs.get('weather_conditions') or ''
                notes = obs.get('notes') or ''
                
                formatted_obs = {
                    'species': str(species),
                    'count': int(count) if count else 1,
                    'location': str(location),
                    'timestamp': str(timestamp),
                    'weather': str(weather),
                    'notes': str(notes)
                }
                formatted_observations.append(formatted_obs)
            except Exception as e:
                logger.warning(f"Error formatting observation: {str(e)}", exc_info=True)
                continue
        
        if not formatted_observations:
            logger.error("No valid observations after formatting")
            return jsonify({
                'error': 'No valid observations to analyze'
            }), 400
        
        # Extract location name from location_data (could be object or string)
        location_name = location_data.get('name') if isinstance(location_data, dict) else str(location_data)
        
        # Generate analysis
        logger.info(f"Calling get_ai_analysis with {len(formatted_observations)} observations for location: {location_name}")
        analysis = tracker.get_ai_analysis(formatted_observations, location_name)
        
        logger.info(f"Analysis result: {analysis[:200] if analysis else 'None'}...")
        
        if not analysis:
            logger.error("No analysis generated")
            return jsonify({
                'error': 'Unable to generate analysis'
            }), 500
        
        logger.info("Analysis generated successfully")
        return jsonify({
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Error in analyze route: {str(e)}", exc_info=True)
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Full traceback: {error_details}")
        
        # Return more details in development mode
        if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_ENV') != 'production':
            return jsonify({
                'error': f'Error generating analysis: {str(e)}',
                'type': type(e).__name__
            }), 500
        else:
            return jsonify({
                'error': 'An unexpected error occurred while generating the analysis.'
            }), 500

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

@bp.route('/analysis')
@login_required
def analysis():
    """Render the AI analysis page with chatbot interface."""
    return render_template('analysis.html')

# Carousel feature removed