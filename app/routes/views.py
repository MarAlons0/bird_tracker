"""View routes for rendering HTML pages."""
from flask import Blueprint, render_template, request, session
from flask_login import login_required, current_user
from flask import current_app

from app.models import Location, UserPreferences
from app.routes.utils import ensure_user_location

views = Blueprint('views', __name__)


@views.before_request
def before_request():
    """Log request information for debugging."""
    current_app.logger.debug(f"Request path: {request.path}")
    current_app.logger.debug(f"User authenticated: {current_user.is_authenticated}")
    if current_user.is_authenticated:
        current_app.logger.debug(f"Current user: {current_user.username}")


@views.route('/')
@login_required
def home():
    """Render the home page with map and bird sightings."""
    try:
        GOOGLE_PLACES_API_KEY = current_app.config.get('GOOGLE_PLACES_API_KEY', '')

        # Get user's current location
        user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        location = None
        if user_pref and user_pref.active_location_id:
            location = Location.query.get(user_pref.active_location_id)

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


@views.route('/profile')
@login_required
def profile():
    """Render the user profile page."""
    return render_template('profile.html')


@views.route('/map')
@login_required
def map():
    """Render the map page showing bird observations for the selected location."""
    user_pref, active_location = ensure_user_location(current_user.id)

    # Get all locations for the user
    locations = Location.query.filter_by(user_id=current_user.id).all()

    return render_template('map.html',
                           active_location=active_location,
                           locations=locations)


@views.route('/analysis')
@login_required
def analysis():
    """Render the AI analysis page with chatbot interface."""
    user_pref, active_location = ensure_user_location(current_user.id)

    # Get all locations for the user
    locations = Location.query.filter_by(user_id=current_user.id).all()

    return render_template('analysis.html',
                           active_location=active_location,
                           locations=locations)
