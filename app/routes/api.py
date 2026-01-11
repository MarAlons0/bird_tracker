"""API routes for data operations."""
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from flask import current_app
from datetime import datetime, timedelta
import os

from app.models import db, User, BirdSighting, Location, UserPreferences, BirdSightingCache
from app.bird_tracker import BirdSightingTracker
from app.routes.utils import get_bird_category

api = Blueprint('api', __name__, url_prefix='/api')


@api.route('/status')
@login_required
def status():
    """Return the application status."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })


@api.route('/stats')
@login_required
def stats():
    """Return basic application statistics."""
    total_users = User.query.count()
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_users = User.query.filter(User.created_at >= week_ago).count()
    return jsonify({
        'total_users': total_users,
        'recent_users': recent_users
    })


@api.route('/sightings')
@login_required
def get_sightings():
    """Return recent bird sightings from eBird API."""
    try:
        lat = request.args.get('lat', type=float)
        lng = request.args.get('lng', type=float)
        radius = request.args.get('radius', type=int)

        if not all([lat, lng, radius]):
            current_app.logger.error("Missing required location parameters")
            return jsonify([])

        current_app.logger.info(f"Fetching sightings for lat: {lat}, lng: {lng}, radius: {radius}")

        if not hasattr(current_app, 'tracker') or current_app.tracker is None:
            current_app.logger.error("BirdSightingTracker not initialized in app")
            return jsonify([])

        tracker = current_app.tracker
        observations = tracker.get_recent_observations_by_location(lat, lng, radius)

        # Transform observations to match the frontend's expected format
        sightings = []
        for obs in observations:
            sightings.append({
                'bird_name': obs.get('comName', 'Unknown'),
                'location': obs.get('locName', 'Unknown'),
                'latitude': obs.get('lat', 0),
                'longitude': obs.get('lng', 0),
                'timestamp': obs.get('obsDt', ''),
                'count': obs.get('howMany', 1),
                'observer': 'eBird User',
                'category': get_bird_category(obs.get('comName', ''))
            })

        return jsonify(sightings)
    except Exception as e:
        current_app.logger.error(f"Error fetching sightings: {e}")
        return jsonify([])


@api.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Generate AI analysis of bird sightings."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        location_data = data.get('location')
        observations = data.get('observations')
        timeframe = int(data.get('timeframe', 7))

        if not location_data:
            return jsonify({'error': 'Location data is required'}), 400

        if not observations:
            return jsonify({'error': 'Observations data is required'}), 400

        current_app.logger.info(f"Generating analysis for location: {location_data}, timeframe: {timeframe} days")

        if not hasattr(current_app, 'tracker') or current_app.tracker is None:
            return jsonify({'error': 'AI service is not available at the moment'}), 503

        tracker = current_app.tracker

        if not tracker.claude:
            return jsonify({'error': 'AI service is not available at the moment'}), 503

        # Format observations for analysis
        formatted_observations = []
        for obs in observations:
            try:
                species = obs.get('bird_name') or obs.get('species') or obs.get('comName') or 'Unknown'
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
                current_app.logger.warning(f"Error formatting observation: {str(e)}")
                continue

        if not formatted_observations:
            return jsonify({'error': 'No valid observations to analyze'}), 400

        location_name = location_data.get('name') if isinstance(location_data, dict) else str(location_data)

        try:
            analysis = tracker.get_ai_analysis(formatted_observations, location_name)
        except Exception as analysis_error:
            current_app.logger.error(f"Error in get_ai_analysis: {str(analysis_error)}")
            return jsonify({'error': f'Error generating analysis: {str(analysis_error)}'}), 500

        if not analysis:
            return jsonify({'error': 'Unable to generate analysis'}), 500

        return jsonify({'analysis': analysis})
    except Exception as e:
        current_app.logger.error(f"Error in analyze route: {str(e)}")
        error_msg = str(e) if os.getenv('FLASK_ENV') != 'production' else 'An unexpected error occurred'
        return jsonify({'error': error_msg}), 500


@api.route('/recent-sightings')
@login_required
def recent_sightings():
    """Return recent bird sightings for the home page."""
    sightings = BirdSighting.query.order_by(BirdSighting.timestamp.desc()).limit(10).all()
    return jsonify([{
        'bird_name': sighting.bird_name,
        'location': sighting.location,
        'timestamp': sighting.timestamp.isoformat()
    } for sighting in sightings])


@api.route('/update-location', methods=['POST'])
@login_required
def update_location():
    """Update the user's location."""
    try:
        data = request.get_json()
        place_id = data.get('place_id')
        name = data.get('name')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = data.get('radius', 25)

        # Validate radius
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
                user_id=current_user.id
            )
            db.session.add(location)
        else:
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


@api.route('/user-preferences')
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


@api.route('/refresh-sightings', methods=['POST'])
@login_required
def refresh_sightings():
    """Force refresh of bird sightings cache."""
    try:
        user_prefs = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not user_prefs or not user_prefs.active_location_id:
            return jsonify({'error': 'No active location found'}), 400

        # Delete existing cache
        BirdSightingCache.query.filter_by(
            user_id=current_user.id,
            location_id=user_prefs.active_location_id
        ).delete()
        db.session.commit()

        # Fetch new data
        tracker = current_app.tracker
        observations = tracker.get_recent_observations(current_user.id)

        return jsonify({
            'success': True,
            'message': f'Successfully refreshed {len(observations)} observations'
        })
    except Exception as e:
        current_app.logger.error(f"Error refreshing sightings: {str(e)}")
        return jsonify({'error': str(e)}), 500


@api.route('/chat', methods=['POST'])
@login_required
def chat():
    """Chat with AI about bird sightings."""
    try:
        data = request.get_json()
        message = data.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        current_app.logger.info(f"Processing chat message: {message[:100]}...")

        observations = data.get('observations')

        if not observations:
            # Fetch recent observations for context
            tracker = current_app.tracker
            observations = tracker.get_recent_observations(user_id=current_user.id)

        # Format observations for context
        context = None
        if observations:
            formatted_observations = []
            for obs in observations:
                bird_name = obs.get('comName') or obs.get('bird_name')
                location = obs.get('locName') or obs.get('location')
                timestamp = obs.get('obsDt') or obs.get('timestamp')
                how_many = obs.get('howMany') or obs.get('count', 1)

                if bird_name and location and timestamp:
                    formatted_obs = f"{bird_name} ({how_many}) at {location} on {timestamp}"
                    formatted_observations.append(formatted_obs)

            context = "\n".join(formatted_observations)

        tracker = current_app.tracker
        response = tracker.chat_with_ai(message, context)

        if not response:
            return jsonify({
                'error': 'No response generated',
                'response': 'I apologize, but I was unable to process your question. Please try again.'
            }), 500

        return jsonify({'response': response})

    except Exception as e:
        current_app.logger.error(f"Chat error: {str(e)}")
        return jsonify({
            'error': str(e),
            'response': 'I apologize, but I encountered an error. Please try again later.'
        }), 500
