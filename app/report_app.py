from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_login import LoginManager
from flask_session import Session
import redis
import logging
from app.config import Config
from app.models import db, User
from app.scheduler import init_scheduler
from app.routes.main import main
from app.routes.auth import auth
from app.routes.admin import admin
from app.routes.api import api
import os
from datetime import timedelta

logger = logging.getLogger(__name__)

# Initialize extensions
migrate = Migrate()
mail = Mail()
login_manager = LoginManager()
session = Session()

@login_manager.user_loader
def load_user(user_id):
    logger.info(f"Loading user with ID: {user_id}")
    user = User.query.get(int(user_id))
    logger.info(f"User loaded: {user.email if user else 'None'}")
    return user

def create_app(config_class=None):
    """Create and configure the Flask application for report generation."""
    app = Flask(__name__)
    if config_class:
        app.config.from_object(config_class)
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger('app')
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    login_manager.init_app(app)
    session.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'main.login'
    login_manager.login_message_category = 'info'
    
    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(api)
    
    # Initialize Redis connection
    if 'SESSION_REDIS' in app.config and hasattr(app.config['SESSION_REDIS'], 'connection_pool'):
        redis_client = redis.from_url(app.config['SESSION_REDIS'].connection_pool.connection_kwargs['url'])
        app.config['SESSION_REDIS'] = redis_client
    
    # Initialize scheduler in non-testing environment
    if not app.config.get('TESTING'):
        init_scheduler()
    
    # Configure session cookie settings
    app.config['SESSION_COOKIE_SECURE'] = True
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'None'
    
    logger.info("Report app initialized successfully")
    return app

if __name__ == '__main__':
    app = create_app()
    # Only create tables if running directly (not through Gunicorn)
    with app.app_context():
        db.create_all()
    app.run() 