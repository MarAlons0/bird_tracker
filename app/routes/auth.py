from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db
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
            logger.info("User not found in database, checking ALLOWED_EMAILS")
            allowed_emails_str = os.getenv('ALLOWED_EMAILS', '')
            logger.info(f"Raw ALLOWED_EMAILS from env: {allowed_emails_str}")
            if not allowed_emails_str:
                logger.error("ALLOWED_EMAILS environment variable is not set!")
                flash("System configuration error. Please contact support.", "error")
                return render_template('auth/login.html', form=form)
            allowed_emails = [e.strip() for e in allowed_emails_str.split(',')]
            logger.info(f"Processed allowed emails: {allowed_emails}")
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            default_password = os.getenv('DEFAULT_USER_PASSWORD', 'user123')
            logger.info(f"Creating user with default password: {default_password}")
            new_user = User(
                username=username,
                email=f"{username}@example.com",
                password_hash=generate_password_hash(default_password),
                is_admin=False,
                is_active=True,
            )
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Created new user with default password: {username}")
            logger.info(f"Logging in new user: {username}")
            login_user(new_user, remember=form.remember.data)
            logger.info(f"New user logged in successfully: {username}")
            flash("Successfully logged in!", "success")
            session.permanent = True
            logger.info(f"Session details: {dict(session)}")
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