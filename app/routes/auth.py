from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db
from werkzeug.security import generate_password_hash
import logging
import os
import sys
import traceback

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        logger.info(f"Login attempt for email: {email}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        
        try:
            # Log database connection info
            logger.info(f"Database URI: {db.engine.url}")
            logger.info(f"Database tables: {db.engine.table_names()}")
            
            # Check if user exists using SQLAlchemy ORM
            user = User.query.filter_by(email=email).first()
            logger.info(f"User query result: {user}")
            
            if user:
                logger.info(f"User found in database: {email}")
                logger.info(f"User details: id={user.id}, email={user.email}, is_admin={user.is_admin}")
                
                if not user.check_password(password):
                    logger.warning(f"Invalid password for user: {email}")
                    flash("Invalid email or password", "error")
                    return render_template('auth/login.html')
                
                # Check if user is active
                if not user.is_active:
                    logger.warning(f"Inactive user attempt: {email}")
                    flash("Your account is not active. Please contact support.", "error")
                    return render_template('auth/login.html')
                
                # Log user in
                logger.info(f"Logging in user: {email}")
                login_user(user, remember=True)
                logger.info(f"User logged in successfully: {email}")
                flash("Successfully logged in!", "success")
                
                # Set session as permanent
                session.permanent = True
                logger.info(f"Session details: {dict(session)}")
                
                # Redirect to the next page or home
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('main.index')
                logger.info(f"Redirecting to: {next_page}")
                return redirect(next_page)
            
            # For new users, check ALLOWED_EMAILS
            logger.info("User not found in database, checking ALLOWED_EMAILS")
            allowed_emails_str = os.getenv('ALLOWED_EMAILS', '')
            logger.info(f"Raw ALLOWED_EMAILS from env: {allowed_emails_str}")
            
            if not allowed_emails_str:
                logger.error("ALLOWED_EMAILS environment variable is not set!")
                flash("System configuration error. Please contact support.", "error")
                return render_template('auth/login.html')
            
            allowed_emails = [e.strip() for e in allowed_emails_str.split(',')]
            logger.info(f"Processed allowed emails: {allowed_emails}")
            
            if email not in allowed_emails:
                logger.warning(f"Unauthorized login attempt for email: {email}")
                logger.warning(f"Email not found in allowed list: {allowed_emails}")
                flash("Sorry, this email is not authorized to access this application.", "error")
                return render_template('auth/login.html')
            
            # Create new user using SQLAlchemy ORM
            logger.info(f"Creating new user for email: {email}")
            
            # Generate username from email
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user
            default_password = os.getenv('DEFAULT_USER_PASSWORD', 'user123')
            logger.info(f"Creating user with default password: {default_password}")
            
            new_user = User(
                email=email,
                username=username,
                password_hash=generate_password_hash(default_password),
                is_admin=False,
                is_approved=True,
                is_active=True,
                newsletter_subscription=True
            )
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Created new user with default password: {email}")
            
            # Log user in
            logger.info(f"Logging in new user: {email}")
            login_user(new_user, remember=True)
            logger.info(f"New user logged in successfully: {email}")
            flash("Successfully logged in!", "success")
            
            # Set session as permanent
            session.permanent = True
            logger.info(f"Session details: {dict(session)}")
            
            # Redirect to home
            return redirect(url_for('main.index'))
            
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            flash("An error occurred during login. Please try again.", "error")
            return render_template('auth/login.html')
    
    return render_template('auth/login.html')

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@auth.route('/request_registration', methods=['GET', 'POST'])
def request_registration():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user:
            flash('Email address already exists')
            return redirect(url_for('auth.request_registration'))
        
        new_user = User(
            email=email,
            username=username,
            password_hash=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        flash('Registration request submitted. Please wait for admin approval.')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/request_registration.html')

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'error')
            return redirect(url_for('auth.change_password'))
        
        if new_password != confirm_password:
            flash('New passwords do not match', 'error')
            return redirect(url_for('auth.change_password'))
        
        current_user.set_password(new_password)
        db.session.commit()
        flash('Password changed successfully', 'success')
        return redirect(url_for('main.index'))
    
    return render_template('auth/change_password.html') 