from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_admin_user(email, password):
    app = create_app()
    with app.app_context():
        try:
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create user
                user = User(
                    email=email,
                    username=email.split('@')[0],
                    is_admin=True,
                    is_approved=True,
                    is_active=True
                )
                user.set_password(password)  # Use the User model's set_password method
                db.session.add(user)
                db.session.commit()
                logger.info(f"Created new admin user: {email}")
            else:
                # Update existing user to be admin
                user.is_admin = True
                user.set_password(password)  # Use the User model's set_password method
                db.session.commit()
                logger.info(f"Updated existing user to admin: {email}")
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            raise

if __name__ == '__main__':
    create_admin_user('alonsoencinci@gmail.com', 'admin123') 