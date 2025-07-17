from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from app.models import db, User, Location, UserPreferences
from flask_mail import Message
from datetime import datetime
from utils.file_upload import save_image, delete_image
import os
from sqlalchemy import text
from werkzeug.utils import secure_filename
from utils.image_processing import process_image, upload_to_cloudinary
from extensions import mail

admin = Blueprint('admin', __name__)

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

@admin.route('/dashboard')
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
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users)

@admin.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    """Admin page for managing users"""
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        
        if action == 'create_user':
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            is_admin_raw = request.form.get('is_admin')
            is_admin = is_admin_raw == 'true'
            
            # Debug logging
            print(f"DEBUG: Creating user with admin rights")
            print(f"DEBUG: username={username}")
            print(f"DEBUG: email={email}")
            print(f"DEBUG: is_admin_raw={is_admin_raw}")
            print(f"DEBUG: is_admin={is_admin}")
            
            # Check if user already exists
            existing_user = db.session.execute(
                text("SELECT id FROM users WHERE username = :username OR email = :email"),
                {"username": username, "email": email}
            ).fetchone()
            
            if existing_user:
                flash('A user with this username or email already exists.', 'error')
            else:
                # Create new user
                db.session.execute(
                    text("""
                        INSERT INTO users (username, email, password_hash, is_admin, is_active, registration_date)
                        VALUES (:username, :email, :password_hash, :is_admin, true, :registration_date)
                    """),
                    {
                        "username": username,
                        "email": email,
                        "password_hash": generate_password_hash(password),
                        "is_admin": is_admin,
                        "registration_date": datetime.utcnow()
                    }
                )
                db.session.commit()
                
                # Ensure Cincinnati exists as a location
                cincinnati = Location.query.filter_by(name='Cincinnati, OH').first()
                if not cincinnati:
                    cincinnati = Location(name='Cincinnati, OH', latitude=39.1031, longitude=-84.5120, radius=25, is_active=True)
                    db.session.add(cincinnati)
                    db.session.commit()
                
                # Create UserPreferences for the new user with Cincinnati as default and active location
                new_user_id = db.session.execute(text("SELECT id FROM users WHERE username = :username"), {"username": username}).fetchone()[0]
                prefs = UserPreferences(user_id=new_user_id, active_location_id=cincinnati.id, default_location_id=cincinnati.id)
                db.session.add(prefs)
                db.session.commit()
                
                flash('User created successfully.', 'success')
                
        elif action == 'toggle_status':
            # Update user status using raw SQL
            db.session.execute(
                text("""
                    UPDATE users
                    SET is_active = NOT is_active
                    WHERE id = :user_id
                """),
                {"user_id": user_id}
            )
            db.session.commit()
            flash('User status updated successfully.', 'success')
                
        elif action == 'delete_user':
            # Delete user using raw SQL
            db.session.execute(
                text("DELETE FROM users WHERE id = :user_id"),
                {"user_id": user_id}
            )
            db.session.commit()
            flash('User deleted successfully.', 'success')
            
        elif action == 'reset_password':
            # Reset user password to default
            default_password = os.getenv('DEFAULT_USER_PASSWORD', 'admin123')
            db.session.execute(
                text("""
                    UPDATE users
                    SET password_hash = :password_hash
                    WHERE id = :user_id
                """),
                {
                    "password_hash": generate_password_hash(default_password),
                    "user_id": user_id
                }
            )
            db.session.commit()
            flash('User password has been reset to default.', 'success')
    
    # Get all users using raw SQL - only query existing columns
    result = db.session.execute(
        text("""
            SELECT id, username, email, password_hash, is_admin, is_active, registration_date, created_at
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
        user.password_hash = row[3]
        user.is_admin = row[4]
        user.is_active = row[5]
        user.registration_date = row[6]
        user.created_at = row[7]
        users.append(user)
    
    return render_template('admin/users.html', users=users)

# Registration requests functionality removed - table no longer exists

# Removed all carousel management routes and logic

# Add this route temporarily to fix user preferences
@admin.route('/fix-preferences/<email>')
@login_required
@admin_required
def fix_preferences(email):
    """Temporary route to fix user preferences"""
    try:
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Get or create Cincinnati location
        cincinnati = Location.query.filter_by(name='Cincinnati, OH').first()
        if not cincinnati:
            cincinnati = Location(
                name='Cincinnati, OH',
                latitude=39.1031,
                longitude=-84.5120,
                radius=25,
                is_active=True
            )
            db.session.add(cincinnati)
            db.session.commit()

        # Get or create user preferences
        prefs = UserPreferences.query.filter_by(user_id=user.id).first()
        if not prefs:
            prefs = UserPreferences(user_id=user.id)
            db.session.add(prefs)

        # Set Cincinnati as both active and default location
        prefs.active_location_id = cincinnati.id
        prefs.default_location_id = cincinnati.id
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Updated preferences for {email} with Cincinnati location',
            'user_id': user.id,
            'preferences_id': prefs.id,
            'location_id': cincinnati.id
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500 