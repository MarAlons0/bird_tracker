# This file makes the app directory a Python package 

from flask import Flask
import os
import logging
from datetime import timedelta
from app.extensions import db, mail, migrate, login_manager

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__, 
                static_folder='static',
                static_url_path='/static')
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///bird_tracker.db')
    if app.config['SQLALCHEMY_DATABASE_URI'].startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLALCHEMY_DATABASE_URI'].replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
    # Secret key configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-secret-key')
    
    # File upload configuration
    app.config['UPLOAD_FOLDER'] = os.path.join(app.static_folder, 'images')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Ensure upload directories exist
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'carousel'), exist_ok=True)
    
    # Google Maps API configuration
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        logger.error("Google Places API Key is not set in environment variables!")
    else:
        logger.info(f"Google Places API Key loaded from environment: {api_key}")
    app.config['GOOGLE_PLACES_API_KEY'] = api_key
    
    # Session configuration
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)
    
    # Initialize extensions
    db.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize the bird tracker
    from app.bird_tracker import BirdSightingTracker
    app.tracker = BirdSightingTracker(app=app)
    app.tracker._initialize_claude()  # Explicitly initialize Claude
    
    # Register blueprints
    from app.routes import main, auth, api
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(api.bp)
    
    logger.info("Application initialized successfully")
    return app

__all__ = ['create_app', 'db'] 