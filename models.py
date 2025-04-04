from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import column_property

class BaseModel(db.Model):
    __abstract__ = True
    
    id = db.Column(db.Integer, primary_key=True)
    
    @declared_attr
    def __tablename__(cls):
        if cls.__name__ == 'User':
            return 'users'
        return cls.__name__.lower()

class Location(db.Model):
    __tablename__ = 'locations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    radius = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=False)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255))  # Updated length to match database
    is_admin = db.Column(db.Boolean, default=False)
    is_approved = db.Column(db.Boolean, default=False)
    registration_date = db.Column(db.DateTime, default=datetime.utcnow)
    _is_active = db.Column('is_active', db.Boolean, default=True)  # Changed to use _is_active as the backing field
    login_token = db.Column(db.String(100), unique=True, nullable=True)
    token_expiry = db.Column(db.DateTime, nullable=True)
    newsletter_subscription = db.Column(db.Boolean, default=True)  # Users are subscribed by default

    # Explicitly tell SQLAlchemy which columns to load
    __mapper_args__ = {
        'include_properties': [
            'id', 'username', 'email', 'password_hash', 'is_admin', 'is_approved',
            'registration_date', '_is_active', 'login_token', 'token_expiry',
            'newsletter_subscription'
        ]
    }

    @property
    def is_active(self):
        """Return whether the user is active."""
        return self._is_active

    @is_active.setter
    def is_active(self, value):
        """Set whether the user is active."""
        self._is_active = value

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        """Set the user's password"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches"""
        return check_password_hash(self.password_hash, password)

class RegistrationRequest(db.Model):
    __tablename__ = 'registration_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

    def __repr__(self):
        return f'<RegistrationRequest {self.username}>'

class CarouselImage(db.Model):
    __tablename__ = 'carouselimage'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    order = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(CarouselImage, self).__init__(**kwargs)
    
    def __repr__(self):
        return f'<CarouselImage {self.filename}>'

class ClaudePromptLog(db.Model):
    __tablename__ = 'claude_prompt_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    prompt_type = db.Column(db.String(50))  # Type of prompt (e.g., 'analysis', 'chat')
    prompt_text = db.Column(db.Text)
    response_text = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    response_length = db.Column(db.Integer)  # Length of the response in characters

class Image(db.Model):
    __tablename__ = 'images'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    filepath = db.Column(db.String(500), nullable=False)  # Will store Cloudinary URL
    upload_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('images', lazy=True))

    def __repr__(self):
        return f'<Image {self.filename}>' 