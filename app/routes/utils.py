"""Utility functions for routes."""
from app.models import db, Location, UserPreferences


def get_bird_category(bird_name):
    """Categorize birds for marker colors based on their common name."""
    bird_name_lower = bird_name.lower()

    # Waterbirds
    waterbirds = [
        'duck', 'goose', 'swan', 'loon', 'grebe', 'heron', 'egret', 'crane', 'pelican',
        'cormorant', 'rail', 'kingfisher', 'gull', 'tern', 'shorebird', 'sandpiper',
        'plover', 'snipe', 'killdeer', 'phalarope', 'stilt', 'avocet', 'coot', 'gallinule'
    ]

    # Raptors
    raptors = [
        'hawk', 'eagle', 'falcon', 'owl', 'vulture', 'kite', 'harrier', 'osprey'
    ]

    # Ground Birds
    ground_birds = [
        'quail', 'grouse', 'turkey', 'dove', 'pigeon', 'roadrunner', 'woodcock'
    ]

    # Aerial Specialists
    aerial_specialists = [
        'hummingbird', 'swift', 'swallow', 'nighthawk', 'flycatcher', 'phoebe', 'pewee'
    ]

    # Tree Specialists
    tree_specialists = [
        'woodpecker', 'sapsucker', 'flicker', 'nuthatch', 'creeper'
    ]

    # Check each category
    if any(term in bird_name_lower for term in waterbirds):
        return 'waterbird'
    elif any(term in bird_name_lower for term in raptors):
        return 'raptor'
    elif any(term in bird_name_lower for term in ground_birds):
        return 'ground_bird'
    elif any(term in bird_name_lower for term in aerial_specialists):
        return 'aerial_specialist'
    elif any(term in bird_name_lower for term in tree_specialists):
        return 'tree_specialist'
    else:
        return 'songbird'  # Default category for Passeriformes


def ensure_user_location(user_id):
    """
    Ensure user has preferences and an active location set.
    Creates default Cincinnati location if needed.

    Returns:
        tuple: (user_preferences, active_location)
    """
    user_pref = UserPreferences.query.filter_by(user_id=user_id).first()

    if not user_pref or not user_pref.active_location_id:
        # Check if Cincinnati location exists
        default_location = Location.query.filter_by(name="Cincinnati, OH").first()

        # If Cincinnati doesn't exist, create it
        if not default_location:
            default_location = Location(
                name="Cincinnati, OH",
                latitude=39.1031,
                longitude=-84.512,
                radius=25,
                is_active=True,
                user_id=user_id
            )
            db.session.add(default_location)
            db.session.flush()

        # Create user preferences if they don't exist
        if not user_pref:
            user_pref = UserPreferences(
                user_id=user_id,
                active_location_id=default_location.id,
                default_location_id=default_location.id
            )
            db.session.add(user_pref)
        else:
            user_pref.active_location_id = default_location.id
            user_pref.default_location_id = default_location.id

        db.session.commit()

    active_location = Location.query.get(user_pref.active_location_id)
    return user_pref, active_location
