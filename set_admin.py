from app import create_app
from app.models import User, db
from werkzeug.security import generate_password_hash
from datetime import datetime

def test_create_admin_user():
    app = create_app()
    with app.app_context():
        # Test creating a user with admin rights
        test_username = "testadmin"
        test_email = "testadmin@example.com"
        test_password = "testpass123"
        is_admin = True
        
        print(f"Testing creation of admin user:")
        print(f"Username: {test_username}")
        print(f"Email: {test_email}")
        print(f"Admin: {is_admin}")
        
        # Check if user already exists
        existing_user = User.query.filter_by(username=test_username).first()
        if existing_user:
            print(f"User {test_username} already exists, deleting...")
            db.session.delete(existing_user)
            db.session.commit()
        
        # Create new user with admin rights
        new_user = User(
            username=test_username,
            email=test_email,
            password_hash=generate_password_hash(test_password),
            is_admin=is_admin,
            is_active=True,
            registration_date=datetime.utcnow()
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✅ Successfully created admin user: {test_username}")
        print(f"User ID: {new_user.id}")
        print(f"Admin status: {new_user.is_admin}")
        
        # Verify the user was created correctly
        created_user = User.query.filter_by(username=test_username).first()
        if created_user:
            print(f"✅ Verification successful - User found in database")
            print(f"Admin status in DB: {created_user.is_admin}")
        else:
            print("❌ Verification failed - User not found in database")

if __name__ == "__main__":
    test_create_admin_user() 