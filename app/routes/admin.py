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

@admin.route('/users', methods=['GET', 'POST'])
@login_required
@admin_required
def users():
    """Admin page for managing users"""
    if request.method == 'POST':
        action = request.form.get('action')
        user_id = request.form.get('user_id')
        
        if action == 'toggle_status':
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

@admin.route('/carousel')
@login_required
@admin_required
def manage_carousel():
    """Admin page for managing carousel images"""
    # Get images from the filesystem
    carousel_dir = os.path.join(current_app.static_folder, 'images', 'carousel')
    filesystem_images = []
    
    if os.path.exists(carousel_dir):
        for filename in os.listdir(carousel_dir):
            if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                # Create a dictionary with image info
                image_info = {
                    'id': len(filesystem_images) + 1,  # Temporary ID
                    'filename': filename,  # Use the actual filename with extension
                    'title': os.path.splitext(filename)[0].replace('_', ' ').title(),
                    'description': '',
                    'order': len(filesystem_images) + 1,
                    'is_active': True,
                    'cloudinary_url': f'https://res.cloudinary.com/dov36rgse/image/upload/v1743815854/carousel/{filename}'  # Add Cloudinary URL
                }
                filesystem_images.append(image_info)
                print(f"Found image: {filename}")  # Debug output
    
    # Get images from database
    try:
        # Create the table if it doesn't exist
        db.session.execute(text("""
            CREATE TABLE IF NOT EXISTS carousel_images (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                title TEXT,
                description TEXT,
                "order" INTEGER,
                is_active BOOLEAN DEFAULT true,
                cloudinary_url TEXT
            )
        """))
        db.session.commit()
        
        result = db.session.execute(text("SELECT * FROM carousel_images ORDER BY \"order\""))
        db_images = [dict(zip(result.keys(), row)) for row in result]
        print(f"Found {len(db_images)} images in database")  # Debug output
    except Exception as e:
        print(f"Database error: {e}")  # Debug output
        db_images = []
    
    # If no images in database but we have filesystem images, add them to database
    if not db_images and filesystem_images:
        print("Adding filesystem images to database")  # Debug output
        for image in filesystem_images:
            try:
                db.session.execute(
                    text("""
                        INSERT INTO carousel_images (filename, title, description, "order", is_active, cloudinary_url)
                        VALUES (:filename, :title, :description, :order, :is_active, :cloudinary_url)
                    """),
                    image
                )
            except Exception as e:
                print(f"Error adding image to database: {e}")
        
        try:
            db.session.commit()
            # Refresh database images after adding them
            result = db.session.execute(text("SELECT * FROM carousel_images ORDER BY \"order\""))
            db_images = [dict(zip(result.keys(), row)) for row in result]
            print(f"Added {len(db_images)} images to database")  # Debug output
        except Exception as e:
            db.session.rollback()
            print(f"Error committing images to database: {e}")
    
    # Use database images if available, otherwise use filesystem images
    images = db_images if db_images else filesystem_images
    
    # Debug output
    print("Available images:", [img['filename'] for img in images])
    
    return render_template('admin/carousel.html', images=images)

@admin.route('/carousel/upload', methods=['POST'])
@login_required
@admin_required
def upload_carousel_image():
    """Handle carousel image upload"""
    if 'image' not in request.files:
        flash('No image file provided', 'error')
        return redirect(url_for('admin.manage_carousel'))
    
    file = request.files['image']
    if file.filename == '':
        flash('No selected file', 'error')
        return redirect(url_for('admin.manage_carousel'))
    
    if file:
        try:
            # Get the next order number
            result = db.session.execute(text("SELECT MAX(\"order\") FROM carousel_images")).fetchone()
            next_order = (result[0] or 0) + 1
            
            # Save the image locally first
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.static_folder, 'images', 'carousel', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            file.save(file_path)
            
            # Upload to Cloudinary
            try:
                from utils.image_processing import upload_to_cloudinary
                cloudinary_url = upload_to_cloudinary(file_path, 'carousel')
                print(f"Uploaded to Cloudinary: {cloudinary_url}")  # Debug output
            except Exception as e:
                print(f"Error uploading to Cloudinary: {e}")  # Debug output
                # Clean up local file
                if os.path.exists(file_path):
                    os.remove(file_path)
                flash('Error uploading image to Cloudinary', 'error')
                return redirect(url_for('admin.manage_carousel'))
            
            # Create database entry
            db.session.execute(
                text("""
                    INSERT INTO carousel_images (filename, title, description, "order", is_active, cloudinary_url)
                    VALUES (:filename, :title, :description, :order, true, :cloudinary_url)
                """),
                {
                    'filename': filename,
                    'title': request.form.get('title', ''),
                    'description': request.form.get('description', ''),
                    'order': next_order,
                    'cloudinary_url': cloudinary_url
                }
            )
            db.session.commit()
            
            flash('Image uploaded successfully', 'success')
        except Exception as e:
            db.session.rollback()
            print(f"Error uploading image: {e}")  # Debug output
            flash(f'Error uploading image: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_carousel'))

@admin.route('/carousel/delete/<int:image_id>', methods=['POST'])
@login_required
@admin_required
def delete_carousel_image(image_id):
    """Delete a carousel image"""
    try:
        # Get the image filename
        result = db.session.execute(
            text("SELECT filename FROM carousel_images WHERE id = :id"),
            {'id': image_id}
        ).fetchone()
        
        if result:
            filename = result[0]
            # Delete the file
            file_path = os.path.join(current_app.static_folder, 'images', 'carousel', filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Delete from database
            db.session.execute(
                text("DELETE FROM carousel_images WHERE id = :id"),
                {'id': image_id}
            )
            db.session.commit()
            flash('Image deleted successfully', 'success')
        else:
            flash('Image not found', 'error')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting image: {str(e)}', 'error')
    
    return redirect(url_for('admin.manage_carousel')) 