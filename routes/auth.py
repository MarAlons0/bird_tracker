from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User
from datetime import datetime, timedelta
import secrets
from flask_mail import Message
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

def test_smtp_connection():
    try:
        server = smtplib.SMTP(os.getenv('MAIL_SERVER'), int(os.getenv('MAIL_PORT')))
        server.starttls()
        server.login(os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
        server.quit()
        logger.info("SMTP connection test successful")
        return True
    except Exception as e:
        logger.error(f"SMTP connection test failed: {str(e)}")
        return False

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        logger.info(f"Login attempt for email: {email}")
        
        # Check if email is in allowed list
        allowed_emails_str = os.getenv('ALLOWED_EMAILS', '')
        logger.info(f"Raw ALLOWED_EMAILS from env: {allowed_emails_str}")
        
        if not allowed_emails_str:
            logger.error("ALLOWED_EMAILS environment variable is not set!")
            return render_template('login.html', 
                error="System configuration error. Please contact support.")
        
        allowed_emails = [e.strip() for e in allowed_emails_str.split(',')]
        logger.info(f"Processed allowed emails: {allowed_emails}")
        
        if email not in allowed_emails:
            logger.warning(f"Unauthorized login attempt for email: {email}")
            logger.warning(f"Email not found in allowed list: {allowed_emails}")
            return render_template('login.html', 
                error="Sorry, this email is not authorized to access this application.")
        
        logger.info(f"Email {email} is authorized")
        
        # Get or create user
        user = User.query.filter_by(email=email).first()
        if not user:
            logger.info(f"Creating new user for email: {email}")
            user = User(email=email)
            db.session.add(user)
            db.session.commit()
        else:
            logger.info(f"Found existing user for email: {email}")
        
        # Generate magic link token
        token = secrets.token_urlsafe(32)
        user.login_token = token
        user.token_expiry = datetime.utcnow() + timedelta(hours=1)
        db.session.commit()
        logger.info(f"Generated login token for user: {email}")
        
        # Test SMTP connection before sending
        if not test_smtp_connection():
            logger.error("SMTP connection test failed, cannot send email")
            return render_template('login.html', 
                error="Failed to connect to email server. Please try again later.")
        
        # Send magic link email
        try:
            # Get the host URL from environment or use the request host
            host_url = os.getenv('HOST_URL', request.host_url.rstrip('/'))
            logger.info(f"Using host URL: {host_url}")
            
            login_url = f"{host_url}/verify/{token}"
            logger.info(f"Generated login URL: {login_url}")
            
            msg = Message('Bird Tracker Login Link',
                         sender=os.getenv('MAIL_USERNAME'),
                         recipients=[email])
            msg.body = f'''Click the following link to log in to Bird Tracker:
{login_url}

This link will expire in 1 hour.'''
            
            # Add detailed debug logging
            logger.info("Email configuration:")
            logger.info(f"MAIL_SERVER: {os.getenv('MAIL_SERVER')}")
            logger.info(f"MAIL_PORT: {os.getenv('MAIL_PORT')}")
            logger.info(f"MAIL_USE_TLS: {os.getenv('MAIL_USE_TLS')}")
            logger.info(f"MAIL_USERNAME: {os.getenv('MAIL_USERNAME')}")
            logger.info(f"Sending to: {email}")
            logger.info(f"Login URL: {login_url}")
            
            from app import mail
            mail.send(msg)
            logger.info("Email sent successfully")
            
            return render_template('check_email.html')
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}", exc_info=True)
            return render_template('login.html', 
                error=f"Failed to send login email: {str(e)}")
        
    return render_template('login.html')

@bp.route('/verify/<token>')
def verify_login(token):
    logger.info(f"Verifying login token: {token}")
    user = User.query.filter_by(login_token=token).first()
    if user and user.token_expiry > datetime.utcnow():
        logger.info(f"Token valid for user: {user.email}")
        login_user(user)
        user.login_token = None  # Invalidate token after use
        db.session.commit()
        return redirect(url_for('main.index'))
    logger.warning(f"Invalid or expired token: {token}")
    return render_template('login.html', error="Invalid or expired login link")

@bp.route('/logout')
@login_required
def logout():
    logger.info(f"User logged out: {current_user.email}")
    logout_user()
    return redirect(url_for('auth.login')) 