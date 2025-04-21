from app import create_app
from app.models import User, db

def check_admin_users():
    app = create_app()
    with app.app_context():
        # Check for admin users
        admin_users = User.query.filter_by(is_admin=True).all()
        print("Current admin users:")
        for user in admin_users:
            print(f"- {user.email} (is_admin: {user.is_admin})")
        
        # Set alonsoencinci@gmail.com as admin if exists
        user = User.query.filter_by(email='alonsoencinci@gmail.com').first()
        if user:
            if not user.is_admin:
                user.is_admin = True
                db.session.commit()
                print(f"\nSet {user.email} as admin")
            else:
                print(f"\n{user.email} is already an admin")
        else:
            print("\nUser alonsoencinci@gmail.com not found")

if __name__ == '__main__':
    check_admin_users() 