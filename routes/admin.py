from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from models import db, User, RegistrationRequest, CarouselImage
from flask_mail import Message
from datetime import datetime
from utils.file_upload import save_image, delete_image
import os
from sqlalchemy import text
from werkzeug.utils import secure_filename
from utils.image_processing import process_image, upload_to_cloudinary

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

@bp.route('/', methods=['GET', 'POST'])
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
                        INSERT INTO users (email, username, password_hash, active, is_admin, is_approved, newsletter_subscription)
                        VALUES (:email, :username, :password_hash, :active, :is_admin, :is_approved, :newsletter_subscription)
                    """),
                    {
                        "email": email,
                        "username": username,
                        "password_hash": generate_password_hash(password),
                        "active": True,
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
                    SET active = NOT active
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

@bp.route('/registration-requests')
@admin_required
def registration_requests():
    # Get registration requests using raw SQL
    result = db.session.execute(
        text("""
            SELECT id, email, notes, status, request_date, processed_at, processed_by
            FROM registration_requests
            ORDER BY request_date DESC
        """)
    ).fetchall()
    
    requests = []
    for row in result:
        request = RegistrationRequest()
        request.id = row[0]
        request.email = row[1]
        request.notes = row[2]
        request.status = row[3]
        request.request_date = row[4]
        request.processed_at = row[5]
        request.processed_by = row[6]
        requests.append(request)
    
    return render_template('admin/registration_requests.html', requests=requests)

@bp.route('/registration-request/<int:request_id>/<action>', methods=['POST'])
@admin_required
def process_registration_request(request_id, action):
    # Get registration request using raw SQL
    result = db.session.execute(
        text("""
            SELECT id, email, notes
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
    request.notes = result[2]
    
    if action == 'approve':
        # Update request status using raw SQL
        db.session.execute(
            text("""
                UPDATE registration_requests
                SET status = 'approved',
                    processed_at = :processed_at,
                    processed_by = :processed_by,
                    notes = :notes
                WHERE id = :request_id
            """),
            {
                "processed_at": datetime.utcnow(),
                "processed_by": current_user.id,
                "notes": f"Approved by {current_user.email}",
                "request_id": request_id
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
        
        You can now complete your registration by visiting:
        {url_for('auth.register', token=request.email, _external=True)}
        
        Best regards,
        The Bird Tracker Team
        """
        current_app.mail.send(msg)
        
        flash('Registration request approved.', 'success')
    
    elif action == 'reject':
        # Update request status using raw SQL
        db.session.execute(
            text("""
                UPDATE registration_requests
                SET status = 'rejected',
                    processed_at = :processed_at,
                    processed_by = :processed_by,
                    notes = :notes
                WHERE id = :request_id
            """),
            {
                "processed_at": datetime.utcnow(),
                "processed_by": current_user.id,
                "notes": f"Rejected by {current_user.email}",
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
        current_app.mail.send(msg)
        
        flash('Registration request rejected.', 'success')
    
    return redirect(url_for('admin.registration_requests'))

# Carousel Image Management
@bp.route('/carousel')
@login_required
@admin_required
def manage_carousel():
    """Admin page for managing carousel images"""
    result = db.session.execute(text("SELECT * FROM carousel_images ORDER BY \"order\""))
    images = [dict(row) for row in result]
    return render_template('admin/carousel.html', images=images)

@bp.route('/carousel/add', methods=['POST'])
@login_required
@admin_required
def add_carousel_image():
    if 'image' not in request.files:
        flash('No image file uploaded', 'error')
        return redirect(url_for('admin.manage_carousel'))

    image_file = request.files['image']
    if image_file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('admin.manage_carousel'))

    title = request.form.get('title')
    description = request.form.get('description')

    try:
        # Process and upload image to Cloudinary
        filename = secure_filename(image_file.filename)
        base_filename = os.path.splitext(filename)[0]
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        new_filename = f"{base_filename}_{timestamp}"
        
        # Process the image
        processed_image = process_image(image_file)
        
        # Upload to Cloudinary with text overlays if title or description is provided
        transformation = []
        if title:
            transformation.append({
                'overlay': {'font_family': 'Arial', 'font_size': 60, 'text': title},
                'color': '#FFFFFF',
                'y': 20,
                'x': 20
            })
        if description:
            transformation.append({
                'overlay': {'font_family': 'Arial', 'font_size': 40, 'text': description},
                'color': '#FFFFFF',
                'y': 100,
                'x': 20
            })
        
        upload_result = upload_to_cloudinary(processed_image, f"carousel/{new_filename}", transformation)
        
        # Get the highest order value using raw SQL
        result = db.session.execute(text("SELECT COALESCE(MAX(\"order\"), -1) FROM carousel_images")).fetchone()
        max_order = result[0]
        
        # Create new carousel image
        new_image = CarouselImage(
            filepath=upload_result['secure_url'],
            filename=new_filename,
            title=title,
            description=description,
            order=max_order + 1,
            is_active=True
        )
        
        db.session.add(new_image)
        db.session.commit()
        
        flash('Image added successfully', 'success')
    except Exception as e:
        flash(f'Error adding image: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_carousel'))

@bp.route('/carousel/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def edit_carousel_image(id):
    image = CarouselImage.query.get_or_404(id)
    
    # Update title and description
    image.title = request.form.get('title')
    image.description = request.form.get('description')
    
    # Update active status
    image.is_active = 'active' in request.form
    
    # If a new image is uploaded
    if 'image' in request.files and request.files['image'].filename:
        try:
            image_file = request.files['image']
            filename = secure_filename(image_file.filename)
            base_filename = os.path.splitext(filename)[0]
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            new_filename = f"{base_filename}_{timestamp}"
            
            # Process the image
            processed_image = process_image(image_file)
            
            # Upload to Cloudinary with text overlays if title or description is provided
            transformation = []
            if image.title:
                transformation.append({
                    'overlay': {'font_family': 'Arial', 'font_size': 60, 'text': image.title},
                    'color': '#FFFFFF',
                    'y': 20,
                    'x': 20
                })
            if image.description:
                transformation.append({
                    'overlay': {'font_family': 'Arial', 'font_size': 40, 'text': image.description},
                    'color': '#FFFFFF',
                    'y': 100,
                    'x': 20
                })
            
            upload_result = upload_to_cloudinary(processed_image, f"carousel/{new_filename}", transformation)
            image.filepath = upload_result['secure_url']
            
        except Exception as e:
            flash(f'Error updating image: {str(e)}', 'error')
            return redirect(url_for('admin.manage_carousel'))
    
    try:
        db.session.commit()
        flash('Image updated successfully', 'success')
    except Exception as e:
        flash(f'Error saving changes: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_carousel'))

@bp.route('/carousel/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_carousel_image(id):
    """Delete a carousel image"""
    image = CarouselImage.query.get_or_404(id)
    
    # Delete from Cloudinary
    if delete_image(image.filename, 'carousel'):
        # Delete the database record
        db.session.delete(image)
        db.session.commit()
        flash('Image deleted successfully', 'success')
    else:
        flash('Error deleting image file', 'error')
    
    return redirect(url_for('admin.manage_carousel'))

@bp.route('/carousel/reorder', methods=['POST'])
@login_required
@admin_required
def reorder_carousel_images():
    """Update the order of carousel images"""
    new_order = request.json.get('order', [])
    
    # Update the order of each image
    for index, image_id in enumerate(new_order):
        image = CarouselImage.query.get(image_id)
        if image:
            image.order = index
    
    db.session.commit()
    return jsonify({'status': 'success'}) 