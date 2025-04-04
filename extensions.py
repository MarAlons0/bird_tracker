from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
scheduler = BackgroundScheduler()

def init_extensions(app):
    # Clear any existing mappers and registry
    clear_mappers()
    mapper_registry.dispose()
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Create a new registry and configure it
    mapper_registry.configure()
    
    @login_manager.user_loader
    def load_user(user_id):
        from models import User  # Import here to avoid circular import
        from flask import current_app
        
        # Create a new session for this operation
        with current_app.app_context():
            try:
                return User.query.get(int(user_id))
            except Exception as e:
                current_app.logger.error(f"Error loading user {user_id}: {str(e)}")
                return None 