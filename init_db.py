from app import app, db
from models import User
import logging
from sqlalchemy import text
import os
from werkzeug.security import generate_password_hash

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with required tables and initial data."""
    print("Database tables created")
    
    # Check if admin user exists
    admin = User.query.filter_by(email='alonsoencinci@gmail.com').first()
    if not admin:
        admin = User(
            email='alonsoencinci@gmail.com',
            password=generate_password_hash(os.getenv('ADMIN_PASSWORD', 'admin123')),
            is_admin=True
        )
        db.session.add(admin)
        print("Created admin user: alonsoencinci@gmail.com")
    
    # Add other users
    users = [
        {
            'email': 'sasandrap@gmail.com',
            'name': 'Sandra Perez Maass',
            'is_admin': False
        },
        {
            'email': 'jalonso91@gmail.com',
            'name': 'Jordi Alonso',
            'is_admin': False
        },
        {
            'email': 'nunualonso96@gmail.com',
            'name': 'Nuria Alonso Perez',
            'is_admin': False
        }
    ]
    
    for user_data in users:
        user = User.query.filter_by(email=user_data['email']).first()
        if not user:
            user = User(
                email=user_data['email'],
                password=generate_password_hash(os.getenv('DEFAULT_USER_PASSWORD', 'user123')),
                is_admin=user_data['is_admin']
            )
            db.session.add(user)
            print(f"Created user: {user_data['email']}")
    
    db.session.commit()

if __name__ == '__main__':
    init_db() 