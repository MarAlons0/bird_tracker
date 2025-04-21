import os
import sys
import json
from app import create_app, db
from app.models import User, Location, UserPreferences

app = create_app()
app.app_context().push()

# Update is_admin flag for alonsoencinci@gmail.com
user = User.query.filter_by(email='alonsoencinci@gmail.com').first()
if user:
    user.is_admin = True
    db.session.commit()
    print(f"Updated is_admin flag for user {user.username}")

# Initialize locations and user preferences for all users
users = User.query.all()
for user in users:
    # Create default location if none exists
    default_location = Location.query.filter_by(user_id=user.id, is_active=True).first()
    if not default_location:
        default_location = Location(
            name='Cincinnati, OH',
            latitude=39.1031,
            longitude=-84.5120,
            radius=10.0,
            is_active=True,
            user_id=user.id
        )
        db.session.add(default_location)
        db.session.commit()
        print(f"Created default location for user {user.username}")

    # Create user preferences if none exists
    preferences = UserPreferences.query.filter_by(user_id=user.id).first()
    if not preferences:
        preferences = UserPreferences(
            user_id=user.id,
            default_location_id=default_location.id,
            notification_enabled=True,
            email_frequency='daily'
        )
        db.session.add(preferences)
        db.session.commit()
        print(f"Created user preferences for user {user.username}")

print("Initialization complete!") 