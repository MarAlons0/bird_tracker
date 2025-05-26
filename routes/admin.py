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

@admin.route('/users')
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

@admin.route('/carousel')
@login_required
@admin_required
def manage_carousel():
    """Admin page for managing carousel images"""
    images = CarouselImage.query.order_by(CarouselImage.order).all()
    return render_template('admin/carousel.html', images=images)

@admin.route('/carousel/add', methods=['POST'])
@login_required
@admin_required
def add_carousel_image():
    """Add a new carousel image"""
    if 'image' not in request.files:
        flash('No image file provided', 'error')
        return redirect(url_for('admin.manage_carousel'))
    
    file = request.files['image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('admin.manage_carousel'))
    
    if file:
        try:
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file)
            image_url = result['secure_url']
            
            # Create new carousel image
            new_image = CarouselImage(
                filename=image_url,
                title=request.form.get('title', '').strip(),
                description=request.form.get('scientific_name', '').strip(),
                is_active=bool(request.form.get('active')),
                order=CarouselImage.query.count() + 1
            )
            
            db.session.add(new_image)
            db.session.commit()
            flash('Bird image added successfully', 'success')
        except Exception as e:
            flash(f'Error adding image: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_carousel'))

@admin.route('/carousel/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_carousel_image(id):
    """Edit an existing carousel image"""
    image = CarouselImage.query.get_or_404(id)
    
    try:
        # Update basic info
        image.title = request.form.get('title', '').strip()
        image.description = request.form.get('scientific_name', '').strip()
        image.is_active = bool(request.form.get('active'))
        
        # Handle new image upload if provided
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            result = cloudinary.uploader.upload(file)
            image.filename = result['secure_url']
        
        db.session.commit()
        flash('Bird image updated successfully', 'success')
    except Exception as e:
        flash(f'Error updating image: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_carousel'))

@admin.route('/carousel/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_carousel_image(id):
    """Delete a carousel image"""
    image = CarouselImage.query.get_or_404(id)
    
    try:
        # Delete from Cloudinary if it's a Cloudinary URL
        if 'cloudinary.com' in image.filename:
            public_id = image.filename.split('/')[-1].split('.')[0]
            cloudinary.uploader.destroy(public_id)
        
        db.session.delete(image)
        db.session.commit()
        flash('Bird image deleted successfully', 'success')
    except Exception as e:
        flash(f'Error deleting image: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_carousel'))

@admin.route('/carousel/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_carousel_images():
    """Update the order of carousel images"""
    try:
        order = request.json.get('order', [])
        for index, image_id in enumerate(order, 1):
            image = CarouselImage.query.get(image_id)
            if image:
                image.order = index
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@admin.route('/carousel/bulk-import', methods=['POST'])
@login_required
@admin_required
def bulk_import_scientific_names():
    """Bulk import scientific names for carousel images"""
    try:
        data = request.json.get('names', {})
        for image_id, scientific_name in data.items():
            image = CarouselImage.query.get(image_id)
            if image:
                image.description = scientific_name.strip()
        
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500 