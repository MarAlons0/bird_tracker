from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, db
from werkzeug.security import generate_password_hash
import logging

logger = logging.getLogger(__name__)

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        
        logger.info(f"Login attempt for email: {email}")
        logger.info("Checking if user exists in database...")
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            logger.info(f"User not found in database: {email}")
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))
        
        logger.info(f"User found in database: {email}")
        logger.info(f"Checking password for user: {email}")
        
        if not user.check_password(password):
            logger.info(f"Password check failed for user: {email}")
            flash('Please check your login details and try again.')
            return redirect(url_for('auth.login'))
        
        logger.info(f"Logging in user: {email}")
        login_user(user, remember=remember)
        logger.info(f"User logged in successfully: {email}")
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('main.index')
        
        logger.info(f"Redirecting to: {next_page}")
        return redirect(next_page)
    
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