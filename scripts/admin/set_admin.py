from app import create_app
from app.models import User, db

def set_admin(email):
    app = create_app()
    with app.app_context():
        try:
            user = User.query.filter_by(email=email).first()
            if user:
                user.is_admin = True
                db.session.commit()
                print(f"Successfully set {email} as admin")
            else:
                print(f"User with email {email} not found")
        except Exception as e:
            print(f"Error setting admin status: {str(e)}")

if __name__ == '__main__':
    set_admin('alonsoencinci@gmail.com') 