from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
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
        password = request.form.get('password')
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
            # Set default password for new users
            default_password = os.getenv('DEFAULT_USER_PASSWORD', 'user123')
            user.set_password(default_password)
            db.session.add(user)
            db.session.commit()
            logger.info(f"Created new user with default password: {email}")
        
        # Check password
        if not user.check_password(password):
            logger.warning(f"Invalid password for user: {email}")
            return render_template('login.html', 
                error="Invalid email or password")
        
        # Log user in
        login_user(user)
        logger.info(f"User logged in successfully: {email}")
        flash("Successfully logged in!", "success")
        return redirect(url_for('main.index'))
        
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logger.info(f"User logged out: {current_user.email}")
    session.clear()  # Clear all session data
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))

@bp.route('/google-login')
def google_login():
    # Generate login URL with state parameter
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    login_url = f"{os.getenv('HOST_URL', 'https://bird-tracker-app-9af5a4fb26d3.herokuapp.com')}/auth/callback"
    auth_url = f"{os.getenv('GOOGLE_AUTH_URL')}?client_id={os.getenv('GOOGLE_CLIENT_ID')}&response_type=code&redirect_uri={login_url}&scope=openid%20email%20profile&state={state}"
    return redirect(auth_url)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not email or not password or not confirm_password:
            return render_template('register.html', error="All fields are required")
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        # Check if email is in allowed list
        allowed_emails_str = os.getenv('ALLOWED_EMAILS', '')
        if not allowed_emails_str:
            logger.error("ALLOWED_EMAILS environment variable is not set!")
            return render_template('register.html', 
                error="System configuration error. Please contact support.")
        
        allowed_emails = [e.strip() for e in allowed_emails_str.split(',')]
        if email not in allowed_emails:
            return render_template('register.html', 
                error="Sorry, this email is not authorized to access this application.")
        
        # Check if user already exists
        if User.query.filter_by(email=email).first():
            return render_template('register.html', 
                error="An account with this email already exists")
        
        # Create new user
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Log user in
        login_user(user)
        flash("Registration successful! Welcome to Bird Tracker.", "success")
        return redirect(url_for('main.index'))
    
    return render_template('register.html') 