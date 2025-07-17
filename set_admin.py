from app import create_app
from app.models import User, db

def set_admin():
    app = create_app()
    with app.app_context():
        # Find the user by email
        user = User.query.filter_by(email='alonsoencinci@gmail.com').first()
        
        if user:
            print(f"Found user: {user.email}")
            print(f"Current admin status: {user.is_admin}")
            
            # Set as admin
            user.is_admin = True
            db.session.commit()
            
            print(f"✅ Successfully set {user.email} as admin")
            print(f"New admin status: {user.is_admin}")
        else:
            print("❌ User not found with email: alonsoencinci@gmail.com")
            print("Available users:")
            users = User.query.all()
            for u in users:
                print(f"  - {u.email} (admin: {u.is_admin})")

if __name__ == "__main__":
    set_admin() 