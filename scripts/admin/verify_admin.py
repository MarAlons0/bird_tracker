from app import create_app
from app.models import User, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_admin_user(email):
    app = create_app()
    with app.app_context():
        try:
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if user:
                logger.info(f"Found user: {email}")
                logger.info(f"Current admin status: {user.is_admin}")
                
                # Update user to be admin
                user.is_admin = True
                user.is_active = True
                user.is_approved = True
                db.session.commit()
                
                logger.info(f"Updated user {email} to admin status")
                logger.info(f"New admin status: {user.is_admin}")
                return True
            else:
                logger.error(f"User {email} not found in database")
                return False
                
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False

if __name__ == '__main__':
    verify_admin_user('alonsoencinci@gmail.com') 