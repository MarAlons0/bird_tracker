from flask import Blueprint, render_template, jsonify, request
from app.models import db, User, NewsletterSubscription, BirdSighting
from datetime import datetime, timedelta
from app.bird_tracker import BirdSightingTracker

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

@main.route('/map')
def map():
    """Render the map page."""
    return render_template('map.html')

@main.route('/report')
def report():
    """Render the AI analysis page."""
    return render_template('report.html')

@main.route('/api/status')
def status():
    """Return the application status."""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@main.route('/api/stats')
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
def analyze():
    """Generate AI analysis of bird sightings."""
    data = request.get_json()
    location = data.get('location')
    timeframe = int(data.get('timeframe', 7))
    
    tracker = BirdSightingTracker()
    analysis = tracker.analyze_sightings(location, timeframe)
    
    return jsonify(analysis)

@main.route('/api/recent-sightings')
def recent_sightings():
    """Return recent bird sightings for the home page."""
    with db.session() as session:
        sightings = session.query(BirdSighting).order_by(BirdSighting.timestamp.desc()).limit(10).all()
        return jsonify([{
            'bird_name': sighting.bird_name,
            'location': sighting.location,
            'timestamp': sighting.timestamp.isoformat()
        } for sighting in sightings]) 