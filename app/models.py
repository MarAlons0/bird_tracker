from config.extensions import db
from datetime import datetime, timedelta
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    login_token = db.Column(db.String(100), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
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

class AllowedEmail(db.Model):
    """Model for storing allowed email addresses that can register/login."""
    __tablename__ = 'allowed_emails'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    added_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    notes = db.Column(db.String(255), nullable=True)

    # Relationship to track who added the email
    added_by_user = db.relationship('User', backref='allowed_emails_added', foreign_keys=[added_by])

    def __repr__(self):
        return f'<AllowedEmail {self.email}>'

    @classmethod
    def is_email_allowed(cls, email):
        """Check if an email is in the allowed list and active."""
        return cls.query.filter_by(email=email.lower().strip(), is_active=True).first() is not None

    @classmethod
    def add_email(cls, email, added_by_id=None, notes=None):
        """Add a new allowed email."""
        email = email.lower().strip()
        existing = cls.query.filter_by(email=email).first()
        if existing:
            if not existing.is_active:
                existing.is_active = True
                db.session.commit()
            return existing
        new_email = cls(email=email, added_by=added_by_id, notes=notes)
        db.session.add(new_email)
        db.session.commit()
        return new_email


class Image(db.Model):
    """Model for storing uploaded images."""
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)  # Cloudinary URL
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('images', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Image {self.id}: {self.filename}>' 
