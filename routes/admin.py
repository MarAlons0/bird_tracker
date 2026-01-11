from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from app.models import User, AllowedEmail
from config.extensions import db
from flask_mail import Message
from datetime import datetime
from utils.file_upload import save_image, delete_image
import os
from sqlalchemy import text
from werkzeug.utils import secure_filename
from utils.image_processing import process_image, upload_to_cloudinary
from extensions import mail
import cloudinary
import cloudinary.uploader
import cloudinary.api

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
    
    # Get pending requests count using raw SQL (table may not exist)
    try:
        result = db.session.execute(text("SELECT COUNT(*) FROM registration_requests WHERE status = 'pending'")).fetchone()
        pending_requests = result[0] if result else 0
    except Exception:
        pending_requests = 0
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         pending_requests=pending_requests)

@admin.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    """Admin page for managing users"""
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')

        if action == 'delete_user' and user_id:
            user = User.query.get(user_id)
            if user:
                if user.id == current_user.id:
                    flash('You cannot delete your own account.', 'error')
                else:
                    # Delete related records first
                    from app.models import UserPreferences
                    UserPreferences.query.filter_by(user_id=user.id).delete()
                    db.session.delete(user)
                    db.session.commit()
                    flash(f'User {user.username} has been deleted.', 'success')

        elif action == 'toggle_admin' and user_id:
            user = User.query.get(user_id)
            if user:
                if user.id == current_user.id:
                    flash('You cannot modify your own admin status.', 'error')
                else:
                    user.is_admin = not user.is_admin
                    db.session.commit()
                    status = 'granted' if user.is_admin else 'revoked'
                    flash(f'Admin rights {status} for {user.username}.', 'success')

        elif action == 'toggle_status' and user_id:
            user = User.query.get(user_id)
            if user:
                if user.id == current_user.id:
                    flash('You cannot deactivate your own account.', 'error')
                else:
                    user.is_active = not user.is_active
                    db.session.commit()
                    status = 'activated' if user.is_active else 'deactivated'
                    flash(f'User {user.username} has been {status}.', 'success')

    # Get all users using ORM
    users = User.query.order_by(User.id).all()
    return render_template('admin/users.html', users=users)

@admin.route('/', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_panel():
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        
        if action == 'add_user':
            email = request.form.get('email')
            password = request.form.get('password')
            is_admin = request.form.get('is_admin') == 'true'
            
            # Check if user exists using raw SQL
            result = db.session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            ).fetchone()
            
            if result:
                flash('Email already exists.', 'error')
            else:
                # Generate username from email
                username = email.split('@')[0]
                # Ensure username is unique using raw SQL
                base_username = username
                counter = 1
                while db.session.execute(
                    text("SELECT id FROM users WHERE username = :username"),
                    {"username": username}
                ).fetchone():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create user using raw SQL
                db.session.execute(
                    text("""
                        INSERT INTO users (email, username, password_hash, is_active, is_admin, is_approved, newsletter_subscription)
                        VALUES (:email, :username, :password_hash, :is_active, :is_admin, :is_approved, :newsletter_subscription)
                    """),
                    {
                        "email": email,
                        "username": username,
                        "password_hash": generate_password_hash(password),
                        "is_active": True,
                        "is_admin": is_admin,
                        "is_approved": True,
                        "newsletter_subscription": True
                    }
                )
                db.session.commit()
                flash('User added successfully.', 'success')
                
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

@admin.route('/registration-requests')
@login_required
@admin_required
def registration_requests():
    """Admin page for managing registration requests"""
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
        requests.append(request)
    
    return render_template('admin/registration_requests.html', requests=requests)

@admin.route('/registration-request/<int:request_id>/<action>', methods=['POST'])
@login_required
@admin_required
def process_registration_request(request_id, action):
    """Process a registration request (approve/reject)"""
    # Get registration request using raw SQL
    result = db.session.execute(
        text("""
            SELECT id, email, username
            FROM registration_requests
            WHERE id = :request_id
        """),
        {"request_id": request_id}
    ).fetchone()
    
    if not result:
        flash('Registration request not found.', 'error')
        return redirect(url_for('admin.registration_requests'))
    
    request = RegistrationRequest()
    request.id = result[0]
    request.email = result[1]
    request.username = result[2]
    
    if action == 'approve':
        # Update request status using raw SQL
        db.session.execute(
            text("""
                UPDATE registration_requests
                SET status = 'approved'
                WHERE id = :request_id
            """),
            {
                "request_id": request_id
            }
        )
        
        # Create new user using raw SQL
        default_password = os.getenv('DEFAULT_USER_PASSWORD', 'user123')
        db.session.execute(
            text("""
                INSERT INTO users (email, username, password_hash, is_admin, is_approved, is_active, newsletter_subscription)
                VALUES (:email, :username, :password_hash, :is_admin, :is_approved, :is_active, :newsletter_subscription)
            """),
            {
                "email": request.email,
                "username": request.username,
                "password_hash": generate_password_hash(default_password),
                "is_admin": False,
                "is_approved": True,
                "is_active": True,
                "newsletter_subscription": True
            }
        )
        
        db.session.commit()
        
        # Send approval email to user
        msg = Message(
            'Registration Request Approved',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[request.email]
        )
        msg.body = f"""
        Your registration request for Bird Tracker has been approved!
        
        You can now log in with your email and the following temporary password:
        {default_password}
        
        Please change your password after logging in.
        
        Best regards,
        The Bird Tracker Team
        """
        mail.send(msg)
        
        flash('Registration request approved and user created.', 'success')
    
    elif action == 'reject':
        # Update request status using raw SQL
        db.session.execute(
            text("""
                UPDATE registration_requests
                SET status = 'rejected'
                WHERE id = :request_id
            """),
            {
                "request_id": request_id
            }
        )
        db.session.commit()
        
        # Send rejection email to user
        msg = Message(
            'Registration Request Rejected',
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=[request.email]
        )
        msg.body = f"""
        We regret to inform you that your registration request for Bird Tracker has been rejected.
        
        If you believe this is a mistake, please contact the administrator.
        
        Best regards,
        The Bird Tracker Team
        """
        mail.send(msg)
        
        flash('Registration request rejected.', 'success')
    
    return redirect(url_for('admin.registration_requests'))

@admin.route('/allowed-emails', methods=['GET', 'POST'])
@login_required
@admin_required
def allowed_emails():
    """Admin page for managing allowed emails"""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_email':
            email = request.form.get('email', '').lower().strip()
            notes = request.form.get('notes', '').strip()

            if not email or '@' not in email:
                flash('Please enter a valid email address.', 'error')
            else:
                existing = AllowedEmail.query.filter_by(email=email).first()
                if existing:
                    if not existing.is_active:
                        existing.is_active = True
                        existing.notes = notes or existing.notes
                        db.session.commit()
                        flash(f'Email {email} has been reactivated.', 'success')
                    else:
                        flash(f'Email {email} is already in the allowed list.', 'warning')
                else:
                    new_allowed = AllowedEmail(
                        email=email,
                        added_by=current_user.id,
                        notes=notes
                    )
                    db.session.add(new_allowed)
                    db.session.commit()
                    flash(f'Email {email} has been added to the allowed list.', 'success')

        elif action == 'toggle_status':
            email_id = request.form.get('email_id')
            allowed_email_obj = AllowedEmail.query.get(email_id)
            if allowed_email_obj:
                allowed_email_obj.is_active = not allowed_email_obj.is_active
                db.session.commit()
                status = 'activated' if allowed_email_obj.is_active else 'deactivated'
                flash(f'Email {allowed_email_obj.email} has been {status}.', 'success')

        elif action == 'delete_email':
            email_id = request.form.get('email_id')
            allowed_email_obj = AllowedEmail.query.get(email_id)
            if allowed_email_obj:
                email_addr = allowed_email_obj.email
                db.session.delete(allowed_email_obj)
                db.session.commit()
                flash(f'Email {email_addr} has been removed from the allowed list.', 'success')

        elif action == 'import_from_env':
            allowed_emails_str = os.getenv('ALLOWED_EMAILS', '')
            if allowed_emails_str:
                emails_list = [e.strip().lower() for e in allowed_emails_str.split(',')]
                imported = 0
                for email in emails_list:
                    if email and '@' in email:
                        existing = AllowedEmail.query.filter_by(email=email).first()
                        if not existing:
                            new_allowed = AllowedEmail(
                                email=email,
                                added_by=current_user.id,
                                notes='Imported from environment variable'
                            )
                            db.session.add(new_allowed)
                            imported += 1
                db.session.commit()
                flash(f'Imported {imported} new email(s) from environment variable.', 'success')
            else:
                flash('No ALLOWED_EMAILS environment variable found.', 'warning')

    # Get all allowed emails
    emails = AllowedEmail.query.order_by(AllowedEmail.created_at.desc()).all()
    return render_template('admin/allowed_emails.html', emails=emails)