from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash

def create_admin_user(email, password):
    app = create_app()
    with app.app_context():
        try:
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create user
                user = User(
                    email=email,
                    username=email.split('@')[0],
                    password_hash=generate_password_hash(password),
                    is_admin=True,
                    is_approved=True,
                    is_active=True
                )
                db.session.add(user)
                db.session.commit()
                print(f"Created new admin user: {email}")
            else:
                # Update existing user to be admin
                user.is_admin = True
                user.password_hash = generate_password_hash(password)
                db.session.commit()
                print(f"Updated existing user to admin: {email}")
        except Exception as e:
            print(f"Error: {str(e)}")

if __name__ == '__main__':
    create_admin_user('alonsoencinci@gmail.com', 'admin123') 