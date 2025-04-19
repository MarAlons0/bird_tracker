from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import Config
from app.models import db
from app.scheduler import init_scheduler
from app.routes.main import main
import os
import logging
from flask_migrate import Migrate

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application for report generation."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Ensure we're using PostgreSQL
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        raise ValueError("DATABASE_URL environment variable is required")
    
    # Fix database URI if needed
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri.replace('postgres://', 'postgresql://')
    
    # Initialize extensions
    db.init_app(app)
    mail = Mail(app)
    migrate = Migrate(app, db)
    
    # Register blueprints
    app.register_blueprint(main)
    
    # Initialize scheduler in non-testing environment
    if not app.config.get('TESTING'):
        init_scheduler()
    
    logger.info("Report app initialized successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    # Only create tables if running directly (not through Gunicorn)
    with app.app_context():
        db.create_all()
    app.run() 