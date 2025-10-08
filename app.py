from flask import Flask, render_template, jsonify, request, url_for, redirect, flash, send_file
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import sys
import os
import json
import logging
from dotenv import load_dotenv
try:
    from config.logging_config import setup_logging
except ImportError:
    def setup_logging():
        pass
import anthropic
import secrets
from flask_mail import Mail, Message
import configparser
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from apscheduler.schedulers.background import BackgroundScheduler
from anthropic import Anthropic
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from extensions import migrate, init_extensions, login_manager, mail, db
from bird_tracker import BirdSightingTracker
import cloudinary
import cloudinary.uploader
import cloudinary.api
from io import BytesIO
import base64
from sqlalchemy.sql import text
import psycopg
from app.models import User, CarouselImage, Location, RegistrationRequest

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import bird_tracker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    print("Starting app creation...")
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static'))
    print(f"Template directory: {template_dir}")
    print(f"Static directory: {static_dir}")
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    print("Flask app created")
    print("Template folder:", os.path.abspath(app.template_folder))
    print("Available templates:", os.listdir(app.template_folder))
    print("Admin templates:", os.listdir(os.path.join(app.template_folder, 'admin')))
    
    # Configure the app
    print("Configuring app...")
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///bird_tracker.db')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['TEMPLATES_AUTO_RELOAD'] = True  # Enable template auto-reloading
    app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable static file caching
    app.jinja_env.auto_reload = True  # Enable Jinja2 auto-reloading
    app.jinja_env.cache_size = 0  # Disable Jinja2 template cache
    print("Basic app configuration complete")

    # Configure session settings for Safari
    print("Configuring session settings...")
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    print("Session settings configured")
    
    # Configure Flask-Mail
    print("Configuring Flask-Mail...")
    app.config['MAIL_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', '587'))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('SMTP_USER')
    app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('SMTP_USER')
    print("Flask-Mail configured")
    
    # Initialize extensions
    print("Initializing extensions...")
    init_extensions(app)
    print("Extensions initialized")
    
    # Configure CORS
    print("Configuring CORS...")
    if os.getenv('FLASK_ENV') == 'production':
        cors = CORS(app, resources={
            r"/*": {
                "origins": ["https://bird-tracker-app-9af5a4fb26d3.herokuapp.com"],
                "supports_credentials": True,
                "allow_headers": ["Content-Type", "Authorization"],
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
            }
        })
    else:
        cors = CORS(app, supports_credentials=True)
    print("CORS configured")
    
    # Register blueprints
    print("Registering blueprints...")
    from routes import main, auth, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.admin, url_prefix='/admin')
    print("Blueprints registered")
    
    # Initialize bird tracker
    print("Initializing bird tracker...")
    app.tracker = BirdSightingTracker()
    print("Bird tracker initialized")
    
    # Configure Cloudinary
    print("Configuring Cloudinary...")
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    print("Cloudinary configured")
    
    print("App creation complete")
    return app

# Create the Flask application
app = create_app()

def init_db():
    with app.app_context():
        try:
            # Ensure we're using the correct database
            db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bird_tracker.db')
            app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
            
            # Drop all tables
            db.drop_all()
            
            # Import models here to ensure they are registered before db.create_all()
            from app.models import User, CarouselImage, Location, RegistrationRequest
            
            # Create all tables
            db.create_all()
            
            # Create admin user
            admin_email = os.getenv('ADMIN_EMAIL')
            admin_password = os.getenv('ADMIN_PASSWORD')
            if admin_email and admin_password:
                admin = User(
                    email=admin_email,
                    username="admin",
                    password_hash=generate_password_hash(admin_password),
                    is_admin=True,
                    is_approved=True,
                    is_active=True,
                    newsletter_subscription=True
                )
                db.session.add(admin)
                print(f"Created admin user: {admin_email}")
            
            # Create default locations
            default_locations = [
                {
                    "name": "Cincinnati",
                    "latitude": 39.1031,
                    "longitude": -84.5120,
                    "radius": 25.0,
                    "is_active": True
                },
                {
                    "name": "Zion National Park",
                    "latitude": 37.2982,
                    "longitude": -113.0263,
                    "radius": 25.0,
                    "is_active": True
                },
                {
                    "name": "Cincinnati Nature Center",
                    "latitude": 39.1753,
                    "longitude": -84.2747,
                    "radius": 5.0,
                    "is_active": True
                },
                {
                    "name": "Moab",
                    "latitude": 38.5733,
                    "longitude": -109.5498,
                    "radius": 25.0,
                    "is_active": True
                },
                {
                    "name": "Zion Nat'l Pk Entrance",
                    "latitude": 37.2017,
                    "longitude": -112.9872,
                    "radius": 5.0,
                    "is_active": True
                },
                {
                    "name": "Bryce Canyon Visitor Ctr",
                    "latitude": 37.6283,
                    "longitude": -112.1687,
                    "radius": 5.0,
                    "is_active": True
                },
                {
                    "name": "Denver",
                    "latitude": 39.7392,
                    "longitude": -104.9903,
                    "radius": 25.0,
                    "is_active": True
                },
                {
                    "name": "Baton Rouge",
                    "latitude": 30.4515,
                    "longitude": -91.1871,
                    "radius": 25.0,
                    "is_active": True
                }
            ]

            for location_data in default_locations:
                location = Location(
                    name=location_data["name"],
                    latitude=location_data["latitude"],
                    longitude=location_data["longitude"],
                    radius=location_data["radius"],
                    is_active=location_data["is_active"],
                    user_id=None,  # Set user_id to NULL for default locations
                    created_at=datetime.utcnow()  # Add created_at timestamp
                )
                db.session.add(location)
                print(f"Created location: {location_data['name']}")

            db.session.commit()
            print("Database initialization completed")
            
        except Exception as e:
            db.session.rollback()
            print(f"Error during database initialization: {str(e)}")
            raise

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('You need administrator privileges to access this page.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def load_locations():
    try:
        with open('locations.json', 'r') as f:
            return json.load(f)
    except TimeoutError:
        print("Timeout while reading locations.json")
        return []
    except FileNotFoundError:
        print("locations.json not found")
        return []
    except json.JSONDecodeError:
        print("Invalid JSON in locations.json")
        return []
    except Exception as e:
        print(f"Error loading locations: {e}")
        return []

def get_carousel_images():
    """Get active carousel images"""
    try:
        images = CarouselImage.query.filter_by(is_active=True).order_by(CarouselImage.order).all()
        return [{
            'id': img.id,
            'filename': img.cloudinary_url or img.filename,
            'title': img.title,
            'description': img.description,
            'order': img.order,
            'is_active': img.is_active
        } for img in images]
    except Exception as e:
        logger.error(f"Error fetching carousel images: {e}")
        return []

@app.route('/map')
@login_required
def map():
    """Map page route"""
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    observations = app.tracker.get_recent_observations(user_id=current_user.id)
    return render_template('map.html', 
                         observations=observations,
                         location=app.tracker.active_location,
                         google_maps_key=google_places_key)

@app.route('/report')
@login_required
def report():
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    return render_template('report.html',
                         location=app.tracker.active_location,
                         google_maps_key=google_places_key)

@app.route('/api/observations')
@login_required
def get_observations():
    observations = app.tracker.get_recent_observations(current_user.id)
    return jsonify(observations)

@app.route('/api/analysis')
def get_analysis():
    try:
        observations = app.tracker.get_recent_observations(current_user.id if current_user.is_authenticated else None)
        logger.debug(f"Analyzing {len(observations)} observations")
        if not observations:
            return jsonify({
                'analysis': '<p class="alert alert-info">No bird sightings found in the last 21 days for this location.</p>'
            })
        
        try:
            logger.info("Starting AI analysis...")
            analysis = app.tracker.analyze_recent_sightings(observations)
            logger.info(f"AI analysis completed, length: {len(analysis) if analysis else 0}")
            
            if not analysis:
                logger.warning("No analysis returned from analyze_recent_sightings")
                return jsonify({
                    'analysis': '<p class="alert alert-warning">Unable to generate analysis at this time.</p>'
                })
            
            # Verify the response is valid HTML
            if not analysis.strip().startswith('<'):
                analysis = f"<p>{analysis}</p>"
            
            return jsonify({'analysis': analysis})
        except Exception as analysis_error:
            logger.error(f"Analysis generation error: {analysis_error}")
            return jsonify({
                'error': 'Unable to generate analysis at this time. Please try again later.'
            }), 503
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        error_msg = f"Error during analysis: {str(e)}"
        logger.error(error_msg)
        return jsonify({'error': error_msg}), 500

@app.route('/api/analysis/basic')
def get_basic_analysis():
    try:
        observations = app.tracker.get_recent_observations(current_user.id if current_user.is_authenticated else None)
        if not observations:
            return jsonify({
                'analysis': '<p class="alert alert-info">No bird sightings found in the last 21 days for this location.</p>'
            })
        
        basic_analysis = app.tracker._generate_basic_analysis(observations)
        return jsonify({'analysis': basic_analysis})
        
    except Exception as e:
        logger.error(f"Basic analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/location', methods=['POST'])
@login_required
def update_location():
    try:
        data = request.get_json()
        location = data.get('location')
        if not location:
            return jsonify({'error': 'No location provided'}), 400
        
        # Update user's active location
        user_pref = UserPreferences.query.filter_by(user_id=current_user.id).first()
        if not user_pref:
            user_pref = UserPreferences(user_id=current_user.id)
            db.session.add(user_pref)
        
        # Check if location exists
        existing_location = Location.query.filter_by(
            name=location['name'],
            latitude=location['lat'],
            longitude=location['lng']
        ).first()
        
        if existing_location:
            user_pref.active_location_id = existing_location.id
        else:
            # Create new location
            new_location = Location(
                name=location['name'],
                latitude=location['lat'],
                longitude=location['lng'],
                radius=location.get('radius', 25.0),
                is_active=True
            )
            db.session.add(new_location)
            db.session.flush()  # Get the ID of the new location
            user_pref.active_location_id = new_location.id
        
        db.session.commit()
        return jsonify({'message': 'Location updated successfully'})
    except Exception as e:
        logger.error(f"Error updating location: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/email-schedule', methods=['POST'])
def update_email_schedule():
    try:
        hour = request.form.get('hour')
        minute = request.form.get('minute')
        
        if not all([hour, minute]):
            return jsonify({"error": "Missing required fields"}), 400
        
        success = app.tracker.update_email_schedule(hour, minute)
        if success:
            return jsonify({
                "success": True,
                "message": f"Email schedule updated to {hour:02d}:{minute:02d}"
            })
        else:
            return jsonify({
                "error": "Failed to update email schedule"
            }), 500

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/upload_image', methods=['POST'])
@login_required
def upload_image():
    try:
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
        
        if file and allowed_file(file.filename):
            # Upload to Cloudinary
            upload_result = cloudinary.uploader.upload(file)
            
            # Create new image record
            new_image = Image(
                filename=file.filename,
                filepath=upload_result['secure_url'],  # Store Cloudinary URL
                upload_date=datetime.utcnow(),
                user_id=current_user.id
            )
            
            db.session.add(new_image)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Image uploaded successfully',
                'image_url': upload_result['secure_url']
            })
        else:
            return jsonify({'error': 'Invalid file type'}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/get_images')
@login_required
def get_images():
    try:
        images = Image.query.filter_by(user_id=current_user.id).order_by(Image.upload_date.desc()).all()
        return jsonify([{
            'id': img.id,
            'filename': img.filename,
            'filepath': img.filepath,  # This will now be the Cloudinary URL
            'upload_date': img.upload_date.strftime('%Y-%m-%d %H:%M:%S')
        } for img in images])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/delete_image/<int:image_id>', methods=['DELETE'])
@login_required
def delete_image(image_id):
    try:
        image = Image.query.get_or_404(image_id)
        
        # Delete from Cloudinary
        if image.filepath:
            public_id = image.filepath.split('/')[-1].split('.')[0]  # Extract public_id from URL
            cloudinary.uploader.destroy(public_id)
        
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    print("Test route called")
    print("Template folder:", app.template_folder)
    print("Template files:", os.listdir(app.template_folder))
    return render_template('test.html')

# Add error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Bird Tracker Application')
    parser.add_argument('--init-db', action='store_true', help='Initialize the database')
    args = parser.parse_args()

    if args.init_db:
        print("Initializing database...")
        init_db()
        print("Database initialization complete.")
        sys.exit(0)

    print("Starting Flask server...")
    app.run(host='127.0.0.1', port=5001, debug=True)  # Enable debug mode for development 