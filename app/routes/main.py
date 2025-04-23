from flask import Blueprint, render_template, jsonify, request
from app.models import db, User, NewsletterSubscription, BirdSighting, CarouselImage, Location, UserPreferences
from datetime import datetime, timedelta
from app.bird_tracker import BirdSightingTracker
from flask_login import login_required, current_user
from flask import current_app

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Render the main page."""
    try:
        # Get active carousel images ordered by their order field
        current_app.logger.info("Fetching carousel images...")
        carousel_images = CarouselImage.query.filter_by(is_active=True).order_by(CarouselImage.order).all()
        current_app.logger.info(f"Found {len(carousel_images)} carousel images")
        for img in carousel_images:
            current_app.logger.info(f"Image: id={img.id}, title={img.title}, filename={img.filename}, cloudinary_url={img.cloudinary_url}")
        
        # Get API key and ensure it's not None
        api_key = current_app.config.get('GOOGLE_PLACES_API_KEY')
        if not api_key:
            current_app.logger.error("Google Places API Key is not set!")
            api_key = ''  # Set empty string instead of None
        else:
            current_app.logger.info(f"Google Places API Key is set: {api_key}")
        
        return render_template('index.html', 
                             carousel_images=carousel_images,
                             GOOGLE_PLACES_API_KEY=api_key,
                             API_KEY=api_key,
                             config=current_app.config)
    except Exception as e:
        current_app.logger.error(f'Error in index route: {str(e)}')
        return render_template('index.html', 
                             carousel_images=[],
                             GOOGLE_PLACES_API_KEY='',
                             API_KEY='',
                             config={})

@main.route('/profile')
@login_required
def profile():
    """Render the user profile page."""
    return render_template('profile.html')

@main.route('/map')
@login_required
def map():
    """Render the map page."""
    return render_template('map.html')

@main.route('/report')
@login_required
def report():
    """Render the AI analysis page."""
    return render_template('report.html')

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
    """Return recent bird sightings."""
    with db.session() as session:
        sightings = session.query(BirdSighting).order_by(BirdSighting.timestamp.desc()).limit(100).all()
        return jsonify([{
            'bird_name': sighting.bird_name,
            'location': sighting.location,
            'latitude': sighting.latitude,
            'longitude': sighting.longitude,
            'timestamp': sighting.timestamp.isoformat(),
            'observer': sighting.observer
        } for sighting in sightings])

@main.route('/api/analyze', methods=['POST'])
@login_required
def analyze():
    """Generate AI analysis of bird sightings."""
    data = request.get_json()
    location = data.get('location')
    timeframe = int(data.get('timeframe', 7))
    
    tracker = BirdSightingTracker()
    analysis = tracker.analyze_sightings(location, timeframe)
    
    return jsonify(analysis)

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
            return jsonify({
                'location': None
            })

        location = Location.query.get(user_pref.active_location_id)
        if not location:
            return jsonify({
                'location': None
            })

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