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
        mail_port = os.getenv('SMTP_PORT', '587')
        mail_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        mail_username = os.getenv('SMTP_USER')
        mail_password = os.getenv('SMTP_PASSWORD')
        
        logger.info(f"Testing SMTP connection to {mail_server}:{mail_port}")
        logger.info(f"Using username: {mail_username}")
        logger.info(f"Password length: {len(mail_password) if mail_password else 0}")
        
        if not all([mail_server, mail_port, mail_username, mail_password]):
            logger.error("Missing SMTP configuration")
            logger.error(f"Server: {mail_server}")
            logger.error(f"Port: {mail_port}")
            logger.error(f"Username: {mail_username}")
            logger.error(f"Password present: {bool(mail_password)}")
            return False
            
        server = smtplib.SMTP(mail_server, int(mail_port))
        logger.info("SMTP connection established")
        server.starttls()
        logger.info("TLS started")
        server.login(mail_username, mail_password)
        logger.info("Login successful")
        server.quit()
        logger.info("SMTP connection test successful")
        return True
    except Exception as e:
        logger.error(f"SMTP connection test failed: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
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
            host_url = os.getenv('HOST_URL', 'https://bird-tracker-app-9af5a4fb26d3.herokuapp.com')
            logger.info(f"Using host URL: {host_url}")
            
            login_url = f"{host_url}/auth/verify/{token}"
            logger.info(f"Generated login URL: {login_url}")
            
            msg = Message('Bird Tracker Login Link',
                         sender=os.getenv('SMTP_USER'),
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

@bp.route('/auth/verify/<token>')
def verify_login(token):
    logger.info(f"Verifying login token: {token}")
    
    # Check if token exists
    user = User.query.filter_by(login_token=token).first()
    if not user:
        logger.warning(f"Token not found in database: {token}")
        flash("Invalid login link. Please request a new one.", "error")
        return redirect(url_for('auth.login'))
    
    # Check if token is expired
    if user.token_expiry <= datetime.utcnow():
        logger.warning(f"Token expired for user: {user.email}")
        user.login_token = None  # Clear expired token
        db.session.commit()
        flash("Login link has expired. Please request a new one.", "error")
        return redirect(url_for('auth.login'))
    
    # Token is valid, log user in
    logger.info(f"Token valid for user: {user.email}")
    login_user(user)
    user.login_token = None  # Invalidate token after use
    db.session.commit()
    
    # Log successful login
    logger.info(f"User logged in successfully: {user.email}")
    flash("Successfully logged in!", "success")
    return redirect(url_for('main.index'))

@bp.route('/logout')
@login_required
def logout():
    logger.info(f"User logged out: {current_user.email}")
    logout_user()
    return redirect(url_for('auth.login'))

@bp.route('/google-login')
def google_login():
    # Generate login URL with state parameter
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    login_url = f"{os.getenv('HOST_URL', 'https://bird-tracker-app-9af5a4fb26d3.herokuapp.com')}/auth/callback"
    auth_url = f"{os.getenv('GOOGLE_AUTH_URL')}?client_id={os.getenv('GOOGLE_CLIENT_ID')}&response_type=code&redirect_uri={login_url}&scope=openid%20email%20profile&state={state}"
    return redirect(auth_url) 