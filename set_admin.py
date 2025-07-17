from app import create_app
from app.models import User, db

def print_user_info():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email='alonsoencinci@gmail.com').first()
        if user:
            print(f"Email: {user.email}")
            print(f"Username: {user.username}")
            print(f"Admin: {user.is_admin}")
        else:
            print("User not found.")

if __name__ == "__main__":
    print_user_info() 