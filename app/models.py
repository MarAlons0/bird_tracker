from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    login_token = db.Column(db.String(100), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    newsletter_subscription = db.Column(db.Boolean, default=True)
    
    newsletter_subscription_rel = db.relationship('NewsletterSubscription', backref='user', uselist=False)

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class NewsletterSubscription(db.Model):
    __tablename__ = 'newsletter_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_sent = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
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