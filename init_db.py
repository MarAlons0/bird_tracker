from app import create_app, db
from werkzeug.security import generate_password_hash
from app.models import User, Location, UserPreferences
import os
import logging

def init_db():
    app = create_app()
    with app.app_context():
        try:
            # Drop all tables
            db.drop_all()
            
            # Create all tables
            db.create_all()

            print("Database tables created")

            # Create admin user
            admin_email = 'alonsoencinci@gmail.com'
            admin_password = 'admin123'
            
            # Create admin user
            admin = User(
                username='admin',
                email=admin_email,
                password_hash=generate_password_hash(admin_password),
                is_admin=True,
                is_approved=True
            )
            
            db.session.add(admin)
            db.session.commit()
            
            print("Admin user created")
            print("Database initialization completed successfully")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error during database initialization: {str(e)}")
            raise

if __name__ == "__main__":
    init_db() 