from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, RegistrationRequest
from datetime import datetime, timedelta
import secrets
from flask_mail import Message, current_app
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
        
        # Check if user exists in database
        user = User.query.filter_by(email=email).first()
        
        # If user exists, allow login regardless of ALLOWED_EMAILS
        if user:
            logger.info(f"User exists in database: {email}")
            if not user.check_password(password):
                logger.warning(f"Invalid password for user: {email}")
                return render_template('login.html', 
                    error="Invalid email or password")
            
            # Log user in
            login_user(user)
            logger.info(f"User logged in successfully: {email}")
            flash("Successfully logged in!", "success")
            return redirect(url_for('main.index'))
        
        # For new users, check ALLOWED_EMAILS
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
        
        # Create new user
        logger.info(f"Creating new user for email: {email}")
        user = User(email=email)
        # Set default password for new users
        default_password = os.getenv('DEFAULT_USER_PASSWORD', 'user123')
        user.set_password(default_password)
        db.session.add(user)
        db.session.commit()
        logger.info(f"Created new user with default password: {email}")
        
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

@bp.route('/request-registration', methods=['GET', 'POST'])
def request_registration():
    if request.method == 'POST':
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Check if email is already registered and active
        existing_user = User.query.filter_by(email=email).first()
        if existing_user and existing_user.is_active:
            return render_template('request_registration.html', 
                error="This email is already registered.")
        
        # Check if there's already a pending request
        if RegistrationRequest.query.filter_by(email=email, status='pending').first():
            return render_template('request_registration.html', 
                error="A registration request for this email is already pending.")
        
        # Create new registration request
        registration_request = RegistrationRequest(email=email, notes=message)
        db.session.add(registration_request)
        db.session.commit()
        
        # Send email to admin
        admin_email = os.getenv('ADMIN_EMAIL')
        if admin_email:
            msg = Message(
                'New Registration Request',
                sender=os.getenv('SMTP_USER'),
                recipients=[admin_email]
            )
            msg.body = f"""
            A new registration request has been submitted:
            
            Email: {email}
            Message: {message}
            
            To approve or reject this request, please visit:
            {url_for('admin.registration_requests', _external=True)}
            """
            current_app.mail.send(msg)
        
        # Send confirmation email to user
        msg = Message(
            'Registration Request Received',
            sender=os.getenv('SMTP_USER'),
            recipients=[email]
        )
        msg.body = f"""
        Thank you for your interest in Bird Tracker!
        
        We have received your registration request and will review it shortly.
        You will receive an email once your request has been processed.
        
        Best regards,
        The Bird Tracker Team
        """
        current_app.mail.send(msg)
        
        return render_template('request_registration.html', 
            success="Your registration request has been submitted successfully.")
    
    return render_template('request_registration.html')

@bp.route('/register/<token>', methods=['GET', 'POST'])
def register(token):
    # Verify token and get registration request
    request = RegistrationRequest.query.filter_by(
        status='approved',
        email=token
    ).first()
    
    if not request:
        flash("Invalid or expired registration link.", "error")
        return redirect(url_for('auth.request_registration'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not password or not confirm_password:
            return render_template('register.html', error="All fields are required")
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        # Create new user
        user = User(email=request.email)
        user.set_password(password)
        db.session.add(user)
        
        # Update registration request
        request.status = 'completed'
        request.processed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log user in
        login_user(user)
        flash("Registration successful! Welcome to Bird Tracker.", "success")
        return redirect(url_for('main.index'))
    
    return render_template('register.html', email=request.email)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            return render_template('change_password.html', error="All fields are required")
        
        if new_password != confirm_password:
            return render_template('change_password.html', error="New passwords do not match")
        
        # Verify current password
        if not current_user.check_password(current_password):
            return render_template('change_password.html', error="Current password is incorrect")
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        # Log out the user to force them to log in with the new password
        logout_user()
        flash("Password updated successfully! Please log in with your new password.", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('change_password.html') 