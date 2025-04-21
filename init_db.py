from app import create_app, db
from werkzeug.security import generate_password_hash
import psycopg2
import os
import logging

def init_db():
    app = create_app()
    with app.app_context():
        try:
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
                        is_active BOOLEAN DEFAULT FALSE,
                        user_id INTEGER REFERENCES users(id)
                    )
                """)
                
                # Create user_preferences table
                cur.execute("""
                    CREATE TABLE user_preferences (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        default_location_id INTEGER REFERENCES locations(id),
                        notification_enabled BOOLEAN DEFAULT TRUE,
                        email_frequency VARCHAR(20) DEFAULT 'daily',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(user_id)
                    )
                """)

                print("Database tables created")

                # Create admin user
                admin_email = 'alonsoencinci@gmail.com'
                admin_password = 'admin123'
                
                # Hash the password
                password_hash = generate_password_hash(admin_password)
                
                # Insert admin user
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, is_admin, is_approved)
                    VALUES ('admin', %s, %s, TRUE, TRUE)
                """, (admin_email, password_hash))
                
                print("Admin user created")
                
                conn.commit()
                print("Database initialization completed successfully")
                
            except Exception as e:
                conn.rollback()
                print(f"Error during database initialization: {str(e)}")
                raise
                
            finally:
                cur.close()
                conn.close()
                
        except Exception as e:
            print(f"Error connecting to database: {str(e)}")
            raise

if __name__ == "__main__":
    init_db() 