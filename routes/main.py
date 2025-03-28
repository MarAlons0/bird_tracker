from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from models import db, User
from bird_tracker import BirdSightingTracker
import os
import logging

bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)

@bp.route('/')
@login_required
def index():
    try:
        email_schedule = {
            'hour': int(os.getenv('EMAIL_SCHEDULE_HOUR', '7')),
            'minute': int(os.getenv('EMAIL_SCHEDULE_MINUTE', '0'))
        }
        
        # Get carousel images
        image_dir = os.path.join('static', 'images', 'birds')
        carousel_images = []
        if os.path.exists(image_dir):
            carousel_images = [f for f in os.listdir(image_dir) 
                             if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        
        # Get Google Places API key
        google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
        if not google_places_key:
            logger.error("Google Places API key not found!")
            return render_template('error.html', error="Google Places API key not configured")
        
        return render_template('index.html',
                             location=current_app.tracker.active_location,
                             email_schedule=email_schedule,
                             carousel_images=carousel_images,
                             google_maps_key=google_places_key)
    except Exception as e:
        logger.error(f"Error in index route: {e}")
        return render_template('error.html', error=str(e))

@bp.route('/report')
@login_required
def report():
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    return render_template('report.html',
                         location=current_app.tracker.active_location,
                         google_maps_key=google_places_key) 