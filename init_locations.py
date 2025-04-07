from app import create_app
from models import Location, User, UserPreferences, db

def init_locations():
    app = create_app()
    with app.app_context():
        # Get all users
        users = User.query.all()
        
        # Create initial locations for each user
        for user in users:
            locations = [
                {
                    'name': 'Denver Botanic Gardens',
                    'latitude': 39.7320964,
                    'longitude': -104.9612839,
                    'radius': 1.0,
                    'is_active': True,
                    'user_id': user.id
                },
                {
                    'name': 'Cincinnati Nature Center',
                    'latitude': 39.1573,
                    'longitude': -84.2944,
                    'radius': 1.0,
                    'is_active': True,
                    'user_id': user.id
                },
                {
                    'name': 'Zion National Park',
                    'latitude': 37.2982,
                    'longitude': -113.0263,
                    'radius': 5.0,
                    'is_active': True,
                    'user_id': user.id
                }
            ]
            
            # Create locations for this user
            for loc_data in locations:
                location = Location(**loc_data)
                db.session.add(location)
            
            # Set the first location as active in user preferences
            db.session.flush()  # Get the IDs of the new locations
            first_location = Location.query.filter_by(
                user_id=user.id,
                name='Denver Botanic Gardens'
            ).first()
            
            if first_location:
                # Create or update user preferences
                prefs = UserPreferences.query.filter_by(user_id=user.id).first()
                if not prefs:
                    prefs = UserPreferences(user_id=user.id)
                    db.session.add(prefs)
                
                prefs.active_location = first_location
        
        db.session.commit()
        print("Locations initialized successfully for all users")

if __name__ == '__main__':
    init_locations() 