from app import app, db
from models import User
import logging
from sqlalchemy import text
import os
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def init_db():
    with app.app_context():
        # Create tables
        try:
            db.create_all()
            print("Database tables created")
        except Exception as e:
            print(f"Note: Some tables may already exist: {e}")

        # User data
        users_data = [
            {
                'email': 'alonsoencinci@gmail.com',
                'password': os.environ.get('ADMIN_PASSWORD', 'admin123'),
                'is_admin': True,
                'is_active': True
            },
            {
                'email': 'sasandrap@gmail.com',
                'password': os.environ.get('DEFAULT_USER_PASSWORD', 'user123'),
                'is_admin': False,
                'is_active': True
            },
            {
                'email': 'jalonso91@gmail.com',
                'password': os.environ.get('DEFAULT_USER_PASSWORD', 'user123'),
                'is_admin': False,
                'is_active': True
            },
            {
                'email': 'nunualonso96@gmail.com',
                'password': os.environ.get('DEFAULT_USER_PASSWORD', 'user123'),
                'is_admin': False,
                'is_active': True
            }
        ]

        # Create or update users
        for user_data in users_data:
            try:
                with db.session.begin_nested():
                    user = User.query.filter_by(email=user_data['email']).with_for_update().first()
                    
                    if user is None:
                        # Create new user
                        user = User(
                            email=user_data['email'],
                            password=generate_password_hash(user_data['password']),
                            is_admin=user_data['is_admin'],
                            is_active=user_data['is_active']
                        )
                        db.session.add(user)
                        print(f"Created {'admin' if user_data['is_admin'] else ''} user: {user_data['email']}")
                    else:
                        # Update existing user
                        user.password = generate_password_hash(user_data['password'])
                        user.is_admin = user_data['is_admin']
                        user.is_active = user_data['is_active']
                        print(f"Updated {'admin' if user_data['is_admin'] else ''} user: {user_data['email']}")

                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                print(f"User {user_data['email']} already exists")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating/updating user {user_data['email']}: {e}")

if __name__ == '__main__':
    init_db() 