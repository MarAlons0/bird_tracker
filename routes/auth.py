from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from datetime import datetime, timedelta
import secrets
from flask_mail import Message
import os
import logging

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Check if email is in allowed list
        allowed_emails = os.getenv('ALLOWED_EMAILS', '').split(',')
        if email not in allowed_emails:
            return render_template('login.html', 
                error="Sorry, this email is not authorized to access this application.")
        
        # Get or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
        
        # Generate magic link token
        token = secrets.token_urlsafe(32)
        user.login_token = token
        user.token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        
        # Send magic link email
        try:
            login_url = url_for('auth.verify_login', token=token, _external=True)
            msg = Message('Bird Tracker Login Link',
                         sender=os.getenv('MAIL_USERNAME'),
                         recipients=[email])
            msg.body = f'''Click the following link to log in to Bird Tracker:
{login_url}

This link will expire in 1 hour.'''
            
            # Add debug logging
            logger.debug("Email configuration:")
            logger.debug(f"MAIL_SERVER: {os.getenv('MAIL_SERVER')}")
            logger.debug(f"MAIL_PORT: {os.getenv('MAIL_PORT')}")
            logger.debug(f"MAIL_USE_TLS: {os.getenv('MAIL_USE_TLS')}")
            logger.debug(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")
            logger.debug(f"Sending to: {email}")
            logger.debug(f"Login URL: {login_url}")
            
            from app import mail
            mail.send(msg)
            logger.debug("Email sent successfully")
            
            return render_template('check_email.html')
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            return render_template('login.html', 
                error=f"Failed to send login email: {str(e)}")
        
    return render_template('login.html')

@bp.route('/verify/<token>')
def verify_login(token):
    user = User.query.filter_by(login_token=token).first()
    if user and user.token_expiry > datetime.utcnow():
        login_user(user)
        user.login_token = None  # Invalidate token after use
        db.session.commit()
        return redirect(url_for('main.index'))
    return render_template('login.html', error="Invalid or expired login link")

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login')) 