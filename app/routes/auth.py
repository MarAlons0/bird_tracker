from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, AllowedEmail, db
from werkzeug.security import generate_password_hash
from urllib.parse import urlparse
import logging
import os
import sys
import traceback
from sqlalchemy import inspect
from flask import current_app
from app.forms import LoginForm

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
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        logger.info(f"Login attempt for username: {username}")
        logger.info(f"Request method: {request.method}")
        logger.info(f"Request headers: {dict(request.headers)}")
        try:
            logger.info(f"Database URI: {db.engine.url}")
            inspector = inspect(db.engine)
            logger.info(f"Database tables: {inspector.get_table_names()}")
            user = User.query.filter_by(username=username).first()
            logger.info(f"User query result: {user}")
            print(f"Login attempt for {username}: User found: {user is not None}")
            if user:
                logger.info(f"User found in database: {username}")
                logger.info(f"User details: id={user.id}, username={user.username}, is_admin={user.is_admin}")
                if not user.check_password(password):
                    logger.warning(f"Invalid password for user: {username}")
                    print(f"Login failed for {username}: User found: {user is not None}, Password check: {user.check_password(password) if user else False}")
                    flash("Invalid username or password", "error")
                    return render_template('auth/login.html', form=form)
                if not user.is_active:
                    logger.warning(f"Inactive user attempt: {username}")
                    flash("Your account is not active. Please contact support.", "error")
                    return render_template('auth/login.html', form=form)
                logger.info(f"Logging in user: {username}")
                print(f"Password check passed for {username}")
                login_user(user, remember=form.remember.data)
                logger.info(f"User logged in successfully: {username}")
                flash("Successfully logged in!", "success")
                session.permanent = True
                logger.info(f"Session details: {dict(session)}")
                next_page = request.args.get('next')
                if not next_page or urlparse(next_page).netloc != '':
                    next_page = url_for('main.home')
                logger.info(f"Redirecting to: {next_page}")
                return redirect(next_page)
            # User not found - check if this is an allowed email for auto-registration
            logger.info("User not found in database, checking if email is allowed")

            # Treat the username as email if it looks like one
            email_to_check = username if '@' in username else None

            if not email_to_check:
                logger.warning(f"Login failed - user not found and input is not an email: {username}")
                flash("Invalid username or password", "error")
                return render_template('auth/login.html', form=form)

            email_to_check = email_to_check.lower().strip()

            # Check database first for allowed emails
            is_allowed = AllowedEmail.is_email_allowed(email_to_check)

            # Fallback to env var if database table is empty (migration support)
            if not is_allowed:
                allowed_emails_str = os.getenv('ALLOWED_EMAILS', '')
                if allowed_emails_str:
                    allowed_emails = [e.strip().lower() for e in allowed_emails_str.split(',')]
                    is_allowed = email_to_check in allowed_emails
                    logger.info(f"Checked env ALLOWED_EMAILS, is_allowed: {is_allowed}")

            if not is_allowed:
                logger.warning(f"Email not in allowed list: {email_to_check}")
                flash("Your email is not authorized. Please contact an administrator.", "error")
                return render_template('auth/login.html', form=form)

            logger.info(f"Email is allowed, creating new user: {email_to_check}")

            # Generate unique username from email
            base_username = email_to_check.split('@')[0]
            new_username = base_username
            counter = 1
            while User.query.filter_by(username=new_username).first():
                new_username = f"{base_username}{counter}"
                counter += 1

            # Check if provided password meets minimum requirements
            if len(password) < 6:
                flash("Password must be at least 6 characters", "error")
                return render_template('auth/login.html', form=form)

            new_user = User(
                username=new_username,
                email=email_to_check,
                password_hash=generate_password_hash(password),
                is_admin=False,
                is_active=True,
            )
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Created new user: {new_username} with email: {email_to_check}")
            login_user(new_user, remember=form.remember.data)
            logger.info(f"New user logged in successfully: {new_username}")
            flash("Account created successfully! Welcome!", "success")
            session.permanent = True
            return redirect(url_for('main.home'))
        except Exception as e:
            logger.error(f"Error during login: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            flash("An error occurred during login. Please try again.", "error")
            return render_template('auth/login.html', form=form)
    return render_template('auth/login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    try:
        logger.info(f"User logged out: {current_user.username}")
        session.clear()  # Clear all session data
        logout_user()
        flash("You have been logged out.", "success")
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.error(f"Error during logout: {str(e)}")
        flash("An error occurred during logout. Please try again.", "error")
        return redirect(url_for('main.index'))

@auth.route('/request_registration', methods=['GET', 'POST'])
def request_registration():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user:
            flash('Username already exists')
            return redirect(url_for('auth.request_registration'))
        
        new_user = User(
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
        return redirect(url_for('main.home'))
    
    return render_template('auth/change_password.html') 