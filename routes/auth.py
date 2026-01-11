from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import User, AllowedEmail
from app.forms import LoginForm
from config.extensions import db
from datetime import datetime, timedelta
import secrets
from flask_mail import Message, current_app
import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy import text

bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)

@bp.route('/test')
def test():
    """Simple test route to verify server is responding"""
    return "<h1>Auth blueprint is working!</h1>"

def test_smtp_connection():
    try:
        mail_port = os.getenv('SMTP_PORT', '587')
        mail_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        mail_username = os.getenv('SMTP_USER')
        mail_password = os.getenv('SMTP_PASSWORD')
        
        logger.info(f"Testing SMTP connection to {mail_server}:{mail_port}")
        logger.info(f"Using username: {mail_username}")
        logger.info(f"Password length: {len(mail_password) if mail_password else 0}")
        
        if not all([mail_server, mail_port, mail_username, mail_password]):
            logger.error("Missing SMTP configuration")
            logger.error(f"Server: {mail_server}")
            logger.error(f"Port: {mail_port}")
            logger.error(f"Username: {mail_username}")
            logger.error(f"Password present: {bool(mail_password)}")
            return False
            
        server = smtplib.SMTP(mail_server, int(mail_port))
        logger.info("SMTP connection established")
        server.starttls()
        logger.info("TLS started")
        server.login(mail_username, mail_password)
        logger.info("Login successful")
        server.quit()
        logger.info("SMTP connection test successful")
        return True
    except Exception as e:
        logger.error(f"SMTP connection test failed: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error args: {e.args}")
        return False

@bp.route('/login', methods=['GET', 'POST'])
def login():
    try:
        form = LoginForm()
    except Exception as e:
        logger.error(f"Error creating LoginForm: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return f"Error creating form: {str(e)}", 500
    
    if request.method == 'POST':
        # Try to get username or email from form
        username_or_email = request.form.get('username') or request.form.get('email')
        password = request.form.get('password')
        logger.info(f"Login attempt for username/email: {username_or_email}")
        
        # If form has username field, use it
        if form.username.data:
            username_or_email = form.username.data
        
        try:
            # Try to find user by email first, then by username
            user = User.query.filter_by(email=username_or_email).first()
            if not user:
                user = User.query.filter_by(username=username_or_email).first()
            
            if user:
                logger.info(f"User found in database: {user.email}")
                if not user.check_password(password):
                    logger.warning(f"Invalid password for user: {user.email}")
                    flash("Invalid username or password", "error")
                    return render_template('auth/login.html', form=form)
                
                # Log user in
                remember = form.remember.data if form.remember else True
                logger.info(f"Logging in user: {user.email}")
                login_user(user, remember=remember)
                logger.info(f"User logged in successfully: {user.email}")
                flash("Successfully logged in!", "success")
                
                # Set session as permanent
                session.permanent = True
                
                # Redirect to the next page or home
                next_page = request.args.get('next')
                if not next_page or not next_page.startswith('/'):
                    next_page = url_for('main.home')
                logger.info(f"Redirecting to: {next_page}")
                return redirect(next_page)
            
            # For new users, check allowed_emails table in database
            # Use username_or_email as email for new user creation
            email = username_or_email if '@' in username_or_email else None
            if not email:
                logger.warning("Invalid email format for new user")
                flash("Invalid username or password", "error")
                return render_template('auth/login.html', form=form)

            logger.info("User not found in database, checking allowed_emails table")

            # Check if email is in allowed_emails table
            allowed_email = AllowedEmail.query.filter_by(email=email, is_active=True).first()

            if not allowed_email:
                logger.warning(f"Unauthorized login attempt for email: {email}")
                logger.warning(f"Email not found in allowed_emails table")
                flash("Sorry, this email is not authorized to access this application.", "error")
                return render_template('auth/login.html', form=form)

            logger.info(f"Email {email} found in allowed_emails table")
            
            # Create new user using SQLAlchemy ORM
            logger.info(f"Creating new user for email: {email}")
            
            # Generate username from email
            username = email.split('@')[0]
            # Ensure username is unique
            base_username = username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1
            
            # Create user
            default_password = os.getenv('DEFAULT_USER_PASSWORD', 'user123')
            logger.info(f"Creating user with default password: {default_password}")
            
            new_user = User(
                email=email,
                username=username,
                password_hash=generate_password_hash(default_password),
                is_admin=False,
                is_active=True
            )
            db.session.add(new_user)
            db.session.commit()
            logger.info(f"Created new user with default password: {email}")
            
            # Log user in
            remember = form.remember.data if form.remember else True
            logger.info(f"Logging in new user: {email}")
            login_user(new_user, remember=remember)
            logger.info(f"New user logged in successfully: {email}")
            flash("Successfully logged in!", "success")
            
            # Set session as permanent
            session.permanent = True
            
            # Redirect to home
            return redirect(url_for('main.home'))
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            logger.error(f"Error during login ({error_type}): {error_msg}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Show more helpful error in development
            if os.getenv('FLASK_ENV') == 'development' or os.getenv('FLASK_ENV') != 'production':
                flash(f"Error during login: {error_type} - {error_msg}. Check server logs for details.", "error")
            else:
                flash("An error occurred during login. Please try again.", "error")
            return render_template('auth/login.html', form=form)
    
    try:
        return render_template('auth/login.html', form=form)
    except Exception as e:
        logger.error(f"Error rendering login template: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        # Return a simple HTML page with the error for debugging
        return f"""
        <html>
        <body>
            <h1>Login Page Error</h1>
            <p>Error: {str(e)}</p>
            <pre>{traceback.format_exc()}</pre>
            <p>Check server logs for more details.</p>
        </body>
        </html>
        """, 500

@bp.route('/logout')
@login_required
def logout():
    logger.info(f"User logged out: {current_user.email}")
    session.clear()  # Clear all session data
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for('auth.login'))

@bp.route('/google-login')
def google_login():
    # Generate login URL with state parameter
    state = secrets.token_urlsafe(16)
    session['oauth_state'] = state
    login_url = f"{os.getenv('HOST_URL', 'https://bird-tracker-app-9af5a4fb26d3.herokuapp.com')}/auth/callback"
    auth_url = f"{os.getenv('GOOGLE_AUTH_URL')}?client_id={os.getenv('GOOGLE_CLIENT_ID')}&response_type=code&redirect_uri={login_url}&scope=openid%20email%20profile&state={state}"
    return redirect(auth_url)

@bp.route('/request-registration', methods=['GET', 'POST'])
def request_registration():
    if request.method == 'POST':
        email = request.form.get('email')
        message = request.form.get('message')
        
        # Check if email is already registered and active using raw SQL
        result = db.session.execute(
            text("SELECT id, is_active FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()
        
        if result and result[1]:  # is_active is True
            return render_template('request_registration.html', 
                error="This email is already registered.")
        
        # Check if there's already a pending request using raw SQL
        result = db.session.execute(
            text("SELECT id FROM registration_requests WHERE email = :email AND status = 'pending'"),
            {"email": email}
        ).fetchone()
        
        if result:
            return render_template('request_registration.html', 
                error="A registration request for this email is already pending.")
        
        # Generate username from email
        username = email.split('@')[0]
        
        # Ensure username is unique in registration_requests table
        base_username = username
        counter = 1
        while db.session.execute(
            text("SELECT id FROM registration_requests WHERE username = :username"),
            {"username": username}
        ).fetchone():
            username = f"{base_username}{counter}"
            counter += 1
        
        # Create new registration request using raw SQL
        db.session.execute(
            text("""
                INSERT INTO registration_requests (email, username, status, request_date)
                VALUES (:email, :username, :status, :request_date)
            """),
            {
                "email": email,
                "username": username,
                "status": "pending",
                "request_date": datetime.utcnow()
            }
        )
        db.session.commit()
        
        # Send email to admin
        admin_email = os.getenv('ADMIN_EMAIL')
        if admin_email:
            msg = Message(
                'New Registration Request',
                sender=os.getenv('SMTP_USER'),
                recipients=[admin_email]
            )
            msg.body = f"""
            A new registration request has been submitted:
            
            Email: {email}
            Message: {message}
            
            To approve or reject this request, please visit:
            {url_for('admin.registration_requests', _external=True)}
            """
            current_app.mail.send(msg)
        
        # Send confirmation email to user
        msg = Message(
            'Registration Request Received',
            sender=os.getenv('SMTP_USER'),
            recipients=[email]
        )
        msg.body = f"""
        Thank you for your interest in Bird Tracker!
        
        We have received your registration request and will review it shortly.
        You will receive an email once your request has been processed.
        
        Best regards,
        The Bird Tracker Team
        """
        current_app.mail.send(msg)
        
        return render_template('request_registration.html', 
            success="Your registration request has been submitted. You will receive an email once it has been processed.")
            
    return render_template('request_registration.html')

@bp.route('/register/<token>', methods=['GET', 'POST'])
def register(token):
    # Verify token and get registration request
    request = RegistrationRequest.query.filter_by(
        status='approved',
        email=token
    ).first()
    
    if not request:
        flash("Invalid or expired registration link.", "error")
        return redirect(url_for('auth.request_registration'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not password or not confirm_password:
            return render_template('register.html', error="All fields are required")
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        # Create new user
        user = User(email=request.email)
        user.set_password(password)
        db.session.add(user)
        
        # Update registration request
        request.status = 'completed'
        request.processed_at = datetime.utcnow()
        
        db.session.commit()
        
        # Log user in
        login_user(user)
        flash("Registration successful! Welcome to Bird Tracker.", "success")
        return redirect(url_for('main.index'))
    
    return render_template('register.html', email=request.email)

@bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Validate inputs
        if not current_password or not new_password or not confirm_password:
            return render_template('change_password.html', error="All fields are required")
        
        if new_password != confirm_password:
            return render_template('change_password.html', error="New passwords do not match")
        
        # Verify current password
        if not current_user.check_password(current_password):
            return render_template('change_password.html', error="Current password is incorrect")
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        # Log out the user to force them to log in with the new password
        logout_user()
        flash("Password updated successfully! Please log in with your new password.", "success")
        return redirect(url_for('auth.login'))
    
    return render_template('change_password.html') 