from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, User
from bird_tracker import BirdSightingTracker
import os

bp = Blueprint('main', __name__)
tracker = BirdSightingTracker()

@bp.route('/')
@login_required
def index():
    return render_template('index.html')

@bp.route('/report')
@login_required
def report():
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    return render_template('report.html',
                         location=tracker.active_location,
                         google_maps_key=google_places_key) 