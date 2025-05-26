from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from config import Config
from app.models import db
from app.scheduler import init_scheduler
import os
import logging

logger = logging.getLogger(__name__)

def create_app():
    """Create and configure the Flask application for report generation."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Set default database URI if not configured
    if not app.config.get('SQLALCHEMY_DATABASE_URI'):
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bird_tracker.db'
    
    # Fix database URI if needed
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if db_uri and db_uri.startswith('postgres://'):
        app.config['SQLALCHEMY_DATABASE_URI'] = db_uri.replace('postgres://', 'postgresql://')
    
    # Initialize extensions
    db.init_app(app)
    mail = Mail(app)
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    # Initialize scheduler
    init_scheduler()
    
    logger.info("Report app initialized successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    app.run() 