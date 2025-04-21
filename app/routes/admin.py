from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from app.models import db, User, RegistrationRequest, CarouselImage
from flask_mail import Message
from datetime import datetime
from utils.file_upload import save_image, delete_image
import os
from sqlalchemy import text
from werkzeug.utils import secure_filename
from utils.image_processing import process_image, upload_to_cloudinary
from extensions import mail

bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    """Admin dashboard showing overview statistics"""
    # Get total users count using raw SQL
    result = db.session.execute(text("SELECT COUNT(*) FROM users")).fetchone()
    total_users = result[0] if result else 0
    
    # Get active users count using raw SQL
    result = db.session.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).fetchone()
    active_users = result[0] if result else 0
    
    # Get pending requests count using raw SQL
    result = db.session.execute(text("SELECT COUNT(*) FROM registration_requests WHERE status = 'pending'")).fetchone()
    pending_requests = result[0] if result else 0
    
    # Get carousel images counts using raw SQL
    result = db.session.execute(text("SELECT COUNT(*) FROM carousel_images")).fetchone()
    total_carousel_images = result[0] if result else 0
    
    result = db.session.execute(text("SELECT COUNT(*) FROM carousel_images WHERE is_active = true")).fetchone()
    active_carousel_images = result[0] if result else 0
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         pending_requests=pending_requests,
                         total_carousel_images=total_carousel_images,
                         active_carousel_images=active_carousel_images)

@bp.route('/users')
@login_required
@admin_required
def users():
    """Admin page for managing users"""
    # Get all users using raw SQL
    result = db.session.execute(
        text("""
            SELECT id, username, email, is_admin, is_approved, registration_date, is_active,
                   login_token, token_expiry, newsletter_subscription
            FROM users
            ORDER BY id
        """)
    ).fetchall()
    
    users = []
    for row in result:
        user = User()
        user.id = row[0]
        user.username = row[1]
        user.email = row[2]
        user.is_admin = row[3]
        user.is_approved = row[4]
        user.registration_date = row[5]
        user.is_active = row[6]
        user.login_token = row[7]
        user.token_expiry = row[8]
        user.newsletter_subscription = row[9]
        users.append(user)
    
    return render_template('admin/users.html', users=users)

@bp.route('/registration-requests')
@admin_required
def registration_requests():
    # Get registration requests using raw SQL
    result = db.session.execute(
        text("""
            SELECT id, email, username, status, request_date
            FROM registration_requests
            ORDER BY request_date DESC
        """)
    ).fetchall()
    
    requests = []
    for row in result:
        request = RegistrationRequest()
        request.id = row[0]
        request.email = row[1]
        request.username = row[2]
        request.status = row[3]
        request.request_date = row[4]
        # Set processed_at and processed_by to None since they don't exist in the table
        request.processed_at = None
        request.processed_by = None
        requests.append(request)
    
    return render_template('admin/registration_requests.html', requests=requests)

@bp.route('/carousel')
@login_required
@admin_required
def manage_carousel():
    """Admin page for managing carousel images"""
    result = db.session.execute(text("SELECT * FROM carousel_images ORDER BY \"order\""))
    images = [dict(zip(result.keys(), row)) for row in result]
    return render_template('admin/carousel.html', images=images) 