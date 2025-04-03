from flask import Flask, render_template, jsonify, request, url_for, redirect, flash, send_file
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from datetime import datetime, timedelta
import sys
import os
import json
import logging
from dotenv import load_dotenv
from logging_config import setup_logging
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
from extensions import migrate, scheduler, init_extensions, login_manager, mail
from bird_tracker import BirdSightingTracker
import cloudinary
import cloudinary.uploader
import cloudinary.api
from io import BytesIO
import base64
from sqlalchemy.orm import clear_mappers
from sqlalchemy.sql import text
import psycopg2

# Load environment variables
load_dotenv()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Add parent directory to path so we can import bird_tracker
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_app():
    app = Flask(__name__)
    
    # Configure the app
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://localhost/bird_tracker')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Clear SQLAlchemy mapper
    clear_mappers()
    
    # Configure session settings for Safari
    app.config['SESSION_COOKIE_SECURE'] = os.getenv('FLASK_ENV') == 'production'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Configure Flask-Mail
    app.config['MAIL_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', '587'))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.getenv('SMTP_USER')
    app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('SMTP_USER')
    
    # Initialize extensions
    init_extensions(app)
    
    # Configure CORS
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
    
    # Register blueprints
    from routes import main, auth, admin
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(admin.bp, url_prefix='/admin')
    
    # Initialize bird tracker
    app.tracker = BirdSightingTracker()
    
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    
    return app

app = create_app()
CORS(app)  # Enable CORS for all routes

def init_db():
    with app.app_context():
        try:
            # Get database URL from app config
            db_url = app.config['SQLALCHEMY_DATABASE_URI']
            
            # Connect to database
            conn = psycopg2.connect(db_url)
            cur = conn.cursor()
            
            try:
                # Drop all tables
                cur.execute("""
                    DROP TABLE IF EXISTS users CASCADE;
                    DROP TABLE IF EXISTS location CASCADE;
                """)
                
                # Create users table
                cur.execute("""
                    CREATE TABLE users (
                        id SERIAL PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        is_admin BOOLEAN DEFAULT FALSE,
                        is_approved BOOLEAN DEFAULT FALSE,
                        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT TRUE,
                        login_token VARCHAR(100) UNIQUE,
                        token_expiry TIMESTAMP,
                        newsletter_subscription BOOLEAN DEFAULT TRUE
                    )
                """)
                
                # Create location table
                cur.execute("""
                    CREATE TABLE location (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(120),
                        latitude FLOAT,
                        longitude FLOAT,
                        radius FLOAT,
                        is_active BOOLEAN DEFAULT FALSE
                    )
                """)

                print("Database tables created")

                # Create admin user
                admin_email = os.getenv('ADMIN_EMAIL')
                admin_password = os.getenv('ADMIN_PASSWORD')
                if admin_email and admin_password:
                    # Create admin user using raw SQL
                    cur.execute("""
                        INSERT INTO users (email, username, password_hash, is_admin, is_approved, is_active, newsletter_subscription)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        admin_email,
                        "admin",
                        generate_password_hash(admin_password),
                        True,
                        True,
                        True,
                        True
                    ))
                    print(f"Created admin user: {admin_email}")
                
                # Create default locations
                default_locations = [
                    {
                        "name": "Cincinnati",
                        "latitude": 39.1031,
                        "longitude": -84.5120,
                        "radius": 50.0,
                        "is_active": True
                    },
                    {
                        "name": "Zion National Park",
                        "latitude": 37.2982,
                        "longitude": -113.0263,
                        "radius": 50.0,
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
                        "radius": 50.0,
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
                        "radius": 50.0,
                        "is_active": True
                    },
                    {
                        "name": "Baton Rouge",
                        "latitude": 30.4515,
                        "longitude": -91.1871,
                        "radius": 50.0,
                        "is_active": True
                    }
                ]

                for location_data in default_locations:
                    # Create location using raw SQL
                    cur.execute("""
                        INSERT INTO location (name, latitude, longitude, radius, is_active)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (
                        location_data["name"],
                        location_data["latitude"],
                        location_data["longitude"],
                        location_data["radius"],
                        location_data["is_active"]
                    ))
                    print(f"Created location: {location_data['name']}")

                conn.commit()
                print("Database initialization completed")
            except Exception as e:
                print(f"Error during database initialization: {str(e)}")
                conn.rollback()
            finally:
                cur.close()
                conn.close()
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")

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
    image_dir = os.path.join('static', 'images', 'birds')
    print(f"Looking for images in: {image_dir}")
    images = []
    if os.path.exists(image_dir):
        for file in os.listdir(image_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                images.append(file)
        print(f"Found images: {images}")
    else:
        print(f"Directory not found: {image_dir}")
    return sorted(images)

@app.route('/')
@login_required
def home():
    try:
        email_schedule = {
            'hour': int(os.getenv('EMAIL_SCHEDULE_HOUR', '7')),
            'minute': int(os.getenv('EMAIL_SCHEDULE_MINUTE', '0'))
        }
        carousel_images = get_carousel_images()
        google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
        ebird_key = os.getenv('EBIRD_API_KEY')
        
        if not google_places_key:
            logger.error("Google Places API key not found!")
            return render_template('error.html', error="Google Places API key not configured")

        if not ebird_key:
            logger.error("eBird API key not found!")
            return render_template('error.html', error="eBird API key not configured")
        
        observations = app.tracker.get_recent_observations()
        logger.debug(f"Found {len(observations)} recent observations")
        
        return render_template('index.html', 
                             location=app.tracker.active_location,
                             email_schedule=email_schedule,
                             carousel_images=carousel_images,
                             google_maps_key=google_places_key)
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return render_template('error.html', error=str(e))

@app.route('/map')
@login_required
def map():
    google_places_key = os.getenv('GOOGLE_PLACES_API_KEY')
    if not google_places_key:
        return render_template('error.html', error="Google Places API key not configured")
        
    observations = app.tracker.get_recent_observations()
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
    observations = app.tracker.get_recent_observations()
    return jsonify(observations)

@app.route('/api/analysis')
def get_analysis():
    try:
        observations = app.tracker.get_recent_observations()
        logger.debug(f"Analyzing {len(observations)} observations")
        if not observations:
            return jsonify({
                'analysis': '<p class="alert alert-info">No bird sightings found in the last 21 days for this location.</p>'
            })
        
        try:
            logger.info("Starting AI analysis...")
            analysis = app.tracker.analyze_observations(observations)
            logger.info(f"AI analysis completed, length: {len(analysis) if analysis else 0}")
            
            if not analysis:
                logger.warning("No analysis returned from analyze_observations")
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
        observations = app.tracker.get_recent_observations()
        if not observations:
            return jsonify({
                'analysis': '<p class="alert alert-info">No bird sightings found in the last 21 days for this location.</p>'
            })
        
        basic_analysis = app.tracker._generate_basic_analysis(observations, {})
        return jsonify({'analysis': basic_analysis})
        
    except Exception as e:
        logger.error(f"Basic analysis error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/location', methods=['POST'])
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
        app.tracker.set_location(name, lat, lng, radius)
        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message')
        if not message:
            return jsonify({'error': 'No message provided'}), 400

        logger.info(f"Processing chat message: {message}")
        
        # Get recent observations for context
        observations = app.tracker.get_recent_observations()
        logger.info(f"Retrieved {len(observations)} observations for context")
        
        # Use the tracker's chat_with_ai method
        response = app.tracker.chat_with_ai(message, observations)
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

# Add error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return render_template('error.html', error="Internal server error"), 500

if __name__ == '__main__':
    init_db()
    print("Starting Flask server...")
    app.run(host='localhost', port=8000, debug=True) 