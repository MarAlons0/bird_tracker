from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from functools import wraps
from models import db, User, RegistrationRequest
from flask_mail import Message
from datetime import datetime
from flask import current_app

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
            
            if User.query.filter_by(email=email).first():
                flash('Email already exists.', 'error')
            else:
                new_user = User(
                    email=email,
                    password=generate_password_hash(password),
                    is_active=True,
                    is_admin=is_admin
                )
                db.session.add(new_user)
                db.session.commit()
                flash('User added successfully.', 'success')
                
        elif action == 'toggle_status':
            user = User.query.get(user_id)
            if user:
                user.is_active = not user.is_active
                db.session.commit()
                flash(f'User status updated successfully.', 'success')
                
        elif action == 'delete_user':
            user = User.query.get(user_id)
            if user:
                db.session.delete(user)
                db.session.commit()
                flash('User deleted successfully.', 'success')
    
    users = User.query.all()
    return render_template('admin.html', users=users)

@bp.route('/registration-requests')
@admin_required
def registration_requests():
    requests = RegistrationRequest.query.order_by(RegistrationRequest.created_at.desc()).all()
    return render_template('admin/registration_requests.html', requests=requests)

@bp.route('/registration-request/<int:request_id>/<action>', methods=['POST'])
@admin_required
def process_registration_request(request_id, action):
    request = RegistrationRequest.query.get_or_404(request_id)
    
    if action == 'approve':
        request.status = 'approved'
        request.processed_at = datetime.utcnow()
        request.processed_by = current_user.id
        request.notes = f"Approved by {current_user.email}"
        
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
        mail.send(msg)
        
        flash('Registration request approved.', 'success')
    
    elif action == 'reject':
        request.status = 'rejected'
        request.processed_at = datetime.utcnow()
        request.processed_by = current_user.id
        request.notes = f"Rejected by {current_user.email}"
        
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
    
    db.session.commit()
    return redirect(url_for('admin.registration_requests')) 