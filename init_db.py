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
                DROP TABLE IF EXISTS users CASCADE;
                DROP TABLE IF EXISTS location CASCADE;
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
            
            # Create location table
            cur.execute("""
                CREATE TABLE location (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(120),
                    latitude FLOAT,
                    longitude FLOAT,
                    radius FLOAT,
                    is_active BOOLEAN DEFAULT FALSE
                )
            """)

            print("Database tables created")

            # Create default users
            default_users = [
                ("alonsoencinci@gmail.com", "admin123"),
                ("sasandrap@gmail.com", "user123"),
                ("jalonso91@gmail.com", "user123"),
                ("nunualonso96@gmail.com", "user123")
            ]

            for email, password in default_users:
                username = email.split('@')[0]
                # Check if user already exists
                cur.execute("SELECT id FROM users WHERE email = %s", (email,))
                if not cur.fetchone():
                    cur.execute("""
                        INSERT INTO users (email, username, password_hash, is_admin, is_approved, is_active, newsletter_subscription)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        email,
                        username,
                        generate_password_hash(password),
                        email == "alonsoencinci@gmail.com",  # Only first user is admin
                        True,  # All users are approved
                        True,  # All users are active
                        True   # All users are subscribed to newsletter
                    ))
                    print(f"Created user: {email}")

            # Commit the transaction
            conn.commit()
            print("Database initialized successfully")

        except Exception as e:
            print(f"Error initializing database: {e}")
            conn.rollback()
            raise
        finally:
            cur.close()
            conn.close()

if __name__ == "__main__":
    init_db() 