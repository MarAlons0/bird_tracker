from extensions import db
from app import create_app
from app.models import User
from werkzeug.security import generate_password_hash

def create_admin_user():
    app = create_app()
    with app.app_context():
        try:
            # Check if admin user exists
            admin = User.query.filter_by(email='admin@example.com').first()
            
            if not admin:
                # Create admin user
                admin = User(
                    email='admin@example.com',
                    username='admin',
                    password_hash=generate_password_hash('admin123', method='pbkdf2:sha256'),
                    is_admin=True,
                    is_approved=True
                )
                db.session.add(admin)
                db.session.commit()
                print("Admin user created successfully!")
            else:
                print("Admin user already exists!")
        except Exception as e:
            print(f"Error creating admin user: {str(e)}")

if __name__ == '__main__':
    create_admin_user() 