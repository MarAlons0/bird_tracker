from app import create_app
from models import Location, db

def init_locations():
    app = create_app()
    with app.app_context():
        # Create initial locations
        locations = [
            {
                'name': 'Denver Botanic Gardens',
                'latitude': 39.7320964,
                'longitude': -104.9612839,
                'radius': 1.0,
                'is_active': True
            },
            {
                'name': 'Cincinnati Nature Center',
                'latitude': 39.1573,
                'longitude': -84.2944,
                'radius': 1.0,
                'is_active': True
            },
            {
                'name': 'Zion National Park',
                'latitude': 37.2982,
                'longitude': -113.0263,
                'radius': 5.0,
                'is_active': True
            }
        ]
        
        for loc_data in locations:
            location = Location(**loc_data)
            db.session.add(location)
        
        db.session.commit()
        print("Locations initialized successfully")

if __name__ == '__main__':
    init_locations() 