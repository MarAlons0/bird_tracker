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
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), "bird_tracker.db")}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Email configuration
    app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
    app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
    
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