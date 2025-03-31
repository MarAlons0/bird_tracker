from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
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

@bp.route('/map')
@login_required
def map():
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    observations = current_app.tracker.get_recent_observations()
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
            'analysis': '<div class="alert alert-danger">Error generating basic analysis.</div>'
        }), 500

@bp.route('/api/analysis')
@login_required
def ai_analysis():
    try:
        observations = current_app.tracker.get_recent_observations()
        if not observations:
            return jsonify({
                'analysis': '<div class="alert alert-info">No recent observations found.</div>'
            })
        
        # Get AI analysis from the tracker
        analysis = current_app.tracker.generate_ai_analysis()
        
        if not analysis:
            return jsonify({
                'analysis': '<div class="alert alert-warning">Unable to generate AI analysis.</div>'
            })
        
        # Ensure the analysis is properly formatted HTML
        if not isinstance(analysis, str) or not analysis.strip().startswith('<'):
            analysis = f'<div class="alert alert-warning">{analysis}</div>'
        
        return jsonify({'analysis': analysis})
    except Exception as e:
        logger.error(f"Error in AI analysis: {e}")
        # Don't return 503 status code, just return error message
        return jsonify({
            'analysis': '<div class="alert alert-danger">Error generating AI analysis. Please try again later.</div>'
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
        response = current_app.tracker.chat_with_ai(message)
        logger.info(f"Chat response received: {response[:100] if response else 'None'}")
        
        if not response:
            logger.warning("No response generated from chat_with_ai")
            return jsonify({
                'error': 'No response generated',
                'response': 'Sorry, I was unable to process your question.'
            }), 500
        
        return jsonify({'response': response})
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Stack trace: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'response': 'Sorry, there was an error processing your request.'
        }), 500

@bp.route('/api/location', methods=['POST'])
@login_required
def update_location():
    try:
        name = request.form.get('name')
        lat = float(request.form.get('lat'))
        lng = float(request.form.get('lng'))
        radius = int(request.form.get('radius'))
        
        # Validate inputs
        if not all([name, lat, lng, radius]):
            return jsonify({"error": "Missing required fields"}), 400
        
        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
            return jsonify({"error": "Invalid coordinates"}), 400
        
        if not (1 <= radius <= 50):
            return jsonify({"error": "Radius must be between 1 and 50 miles"}), 400

        # Update tracker location
        current_app.tracker.set_location(name, lat, lng, radius)
        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        return jsonify({"error": str(e)}), 500

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