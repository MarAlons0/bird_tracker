from flask import Blueprint, render_template, jsonify
from app.models import db, User, NewsletterSubscription
from datetime import datetime, timedelta

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')

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