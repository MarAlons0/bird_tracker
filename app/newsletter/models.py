from datetime import datetime
from app.extensions import db

class NewsletterSubscription(db.Model):
    """Model for tracking user newsletter subscriptions."""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_sent = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # No relationship to User here
    
    def __repr__(self):
        return f'<NewsletterSubscription {self.user_id}>' 