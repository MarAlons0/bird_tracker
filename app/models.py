from app.extensions import db
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(120), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    login_token = db.Column(db.String(100), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    newsletter_subscription = db.relationship('NewsletterSubscription', back_populates='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class BirdSighting(db.Model):
    __tablename__ = 'bird_sightings'
    
    id = db.Column(db.Integer, primary_key=True)
    bird_name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    observer = db.Column(db.String(255))
    notes = db.Column(db.Text)

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    radius = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    place_id = db.Column(db.String(255), nullable=True)  # For Google Places API
    
    # Define relationships with explicit foreign keys
    user = db.relationship('User', backref=db.backref('locations', lazy='dynamic'))
    
    preferences_as_default = db.relationship('UserPreferences',
                                          foreign_keys='UserPreferences.default_location_id',
                                          backref='default_location')
    
    preferences_as_active = db.relationship('UserPreferences',
                                         foreign_keys='UserPreferences.active_location_id',
                                         backref='active_location')

    def __repr__(self):
        return f'<Location {self.name}>'

class UserPreferences(db.Model):
    __tablename__ = 'user_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    default_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    active_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'))
    notification_enabled = db.Column(db.Boolean, default=True)
    email_frequency = db.Column(db.String(20), default='daily')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('preferences', uselist=False))

    def __repr__(self):
        return f'<UserPreferences for user {self.user_id}>'

class RegistrationRequest(db.Model):
    """Model for handling user registration requests"""
    __tablename__ = 'registration_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    def __repr__(self):
        return f'<RegistrationRequest {self.email}>'

class CarouselImage(db.Model):
    """Model for managing carousel images"""
    __tablename__ = 'carousel_images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255))
    cloudinary_url = db.Column(db.String(255))
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    order = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    filepath = db.Column(db.String(255))
    upload_date = db.Column(db.DateTime)
    user_id = db.Column(db.Integer)
    
    def __repr__(self):
        return f'<CarouselImage {self.title}>'

class BirdSightingCache(db.Model):
    """Cache for eBird observations to reduce API calls."""
    __tablename__ = 'bird_sighting_cache'

    id = db.Column(db.Integer, primary_key=True)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    observations = db.Column(db.JSON, nullable=False)  # Store the full eBird response
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)  # When the cache should be invalidated

    # Relationships
    location = db.relationship('Location', backref='sighting_caches')
    user = db.relationship('User', backref='sighting_caches')

    def __repr__(self):
        return f'<BirdSightingCache {self.id} for location {self.location_id}>'

    @classmethod
    def get_valid_cache(cls, user_id, location_id):
        """Get valid cache entry for user and location."""
        now = datetime.utcnow()
        return cls.query.filter(
            cls.user_id == user_id,
            cls.location_id == location_id,
            cls.expires_at > now
        ).first()

    @classmethod
    def create_cache(cls, user_id, location_id, observations, cache_duration=3600):
        """Create a new cache entry."""
        from flask import current_app
        if user_id is None or location_id is None:
            if hasattr(current_app, 'logger'):
                current_app.logger.warning(f"Skipping cache creation: user_id={user_id}, location_id={location_id}")
            else:
                print(f"[WARNING] Skipping cache creation: user_id={user_id}, location_id={location_id}")
            return None
        now = datetime.utcnow()
        expires_at = now + timedelta(seconds=cache_duration)
        
        # Delete any existing cache for this user and location
        cls.query.filter_by(
            user_id=user_id,
            location_id=location_id
        ).delete()
        
        # Create new cache entry
        cache = cls(
            user_id=user_id,
            location_id=location_id,
            observations=observations,
            expires_at=expires_at
        )
        db.session.add(cache)
        db.session.commit()
        return cache 
