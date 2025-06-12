from app import create_app, db
from app.models import User, UserPreferences, Location

def fix_user_preferences(email):
    app = create_app()
    with app.app_context():
        # Get the user
        user = User.query.filter_by(email=email).first()
        if not user:
            print(f"User {email} not found")
            return

        # Get or create Cincinnati location
        location = Location.query.filter_by(name="Cincinnati, OH").first()
        if not location:
            location = Location(
                name="Cincinnati, OH",
                latitude=39.1031,
                longitude=-84.5120,
                radius=25,
                is_active=True
            )
            db.session.add(location)
            db.session.flush()

        # Get or create user preferences
        prefs = UserPreferences.query.filter_by(user_id=user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=user.id)
            db.session.add(prefs)

        # Set both active and default location to Cincinnati
        prefs.active_location_id = location.id
        prefs.default_location_id = location.id

        try:
            db.session.commit()
            print(f"Successfully updated preferences for {email}")
            print(f"Active Location: {location.name}")
            print(f"Default Location: {location.name}")
        except Exception as e:
            db.session.rollback()
            print(f"Error updating preferences: {str(e)}")

if __name__ == "__main__":
    fix_user_preferences("sasandrap@gmail.com") 