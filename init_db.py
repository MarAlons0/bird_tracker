from app import create_app
from werkzeug.security import generate_password_hash
import psycopg2
import os
import logging

def init_db():
    app = create_app()
    with app.app_context():
        # Get database URL from app config
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        
        # Connect to database
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        try:
            # Drop all tables
            cur.execute("""
                DROP TABLE IF EXISTS user_preferences CASCADE;
                DROP TABLE IF EXISTS locations CASCADE;
                DROP TABLE IF EXISTS users CASCADE;
            """)
            
            # Create users table
            cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_approved BOOLEAN DEFAULT FALSE,
                    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE,
                    login_token VARCHAR(100) UNIQUE,
                    token_expiry TIMESTAMP,
                    newsletter_subscription BOOLEAN DEFAULT TRUE
                )
            """)
            
            # Create locations table
            cur.execute("""
                CREATE TABLE locations (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(120),
                    latitude FLOAT,
                    longitude FLOAT,
                    radius FLOAT,
                    is_active BOOLEAN DEFAULT FALSE
                )
            """)
            
            # Create user_preferences table
            cur.execute("""
                CREATE TABLE user_preferences (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    active_location_id INTEGER REFERENCES locations(id),
                    default_radius FLOAT DEFAULT 50.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id)
                )
            """)

            print("Database tables created")
            
            # Create admin user
            admin_email = os.getenv('ADMIN_EMAIL')
            admin_password = os.getenv('ADMIN_PASSWORD')
            if admin_email and admin_password:
                # Create admin user using raw SQL
                cur.execute("""
                    INSERT INTO users (email, username, password_hash, is_admin, is_approved, is_active, newsletter_subscription)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    admin_email,
                    "admin",
                    generate_password_hash(admin_password),
                    True,
                    True,
                    True,
                    True
                ))
                print(f"Created admin user: {admin_email}")
            
            conn.commit()
            print("Database initialized successfully")
            
        except Exception as e:
            conn.rollback()
            print(f"Error initializing database: {str(e)}")
            raise
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    init_db() 