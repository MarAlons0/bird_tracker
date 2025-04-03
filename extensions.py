from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import clear_mappers, registry
from sqlalchemy import text

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()
scheduler = BackgroundScheduler()
mapper_registry = registry()

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
                # Use raw SQL to load user
                result = db.session.execute(
                    text("""
                        SELECT id, username, email, password_hash, is_admin, is_approved,
                               registration_date, is_active, login_token, token_expiry,
                               newsletter_subscription
                        FROM users
                        WHERE id = :user_id
                    """),
                    {"user_id": int(user_id)}
                ).fetchone()
                
                if result:
                    # Create a User instance with the raw data
                    user = User()
                    user.id = result[0]
                    user.username = result[1]
                    user.email = result[2]
                    user.password_hash = result[3]
                    user.is_admin = result[4]
                    user.is_approved = result[5]
                    user.registration_date = result[6]
                    user._is_active = result[7]
                    user.login_token = result[8]
                    user.token_expiry = result[9]
                    user.newsletter_subscription = result[10]
                    return user
                return None
            except Exception as e:
                current_app.logger.error(f"Error loading user {user_id}: {str(e)}")
                return None 