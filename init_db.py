from app import create_app
from config.extensions import db
from app.models import User, Location, BirdSighting, UserPreferences, AllowedEmail
from werkzeug.security import generate_password_hash
import os

app = create_app()
print(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")
print(f"Current working directory: {os.getcwd()}")

# Check if database file exists
db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
    print(f"Database file exists: {os.path.exists(db_path)}")

with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully!")

    # Verify tables were created
    print("\nVerifying tables...")
    for table in db.metadata.tables:
        print(f"  ✓ {table}")

    # Seed allowed emails if table is empty
    if AllowedEmail.query.count() == 0:
        print("\nSeeding allowed emails...")
        allowed_emails = [
            'alonsoencinci@gmail.com',
            'sasandrap@gmail.com',
            'jalonso91@gmail.com',
            'nunualonso96@gmail.com'
        ]
        for email in allowed_emails:
            allowed = AllowedEmail(email=email, is_active=True, notes='Initial setup')
            db.session.add(allowed)
        db.session.commit()
        print(f"  Added {len(allowed_emails)} allowed emails")

    # Create admin user if no users exist
    if User.query.count() == 0:
        print("\nCreating admin user...")
        admin_email = os.getenv('ADMIN_EMAIL', 'alonsoencinci@gmail.com')
        admin_password = os.getenv('ADMIN_PASSWORD', 'BirdTracker2024')
        admin = User(
            email=admin_email,
            username='Mario',
            password_hash=generate_password_hash(admin_password),
            is_admin=True,
            is_active=True
        )
        db.session.add(admin)
        db.session.commit()
        print(f"  Created admin user: {admin_email}")

    print("\n✅ Database initialization complete!") 