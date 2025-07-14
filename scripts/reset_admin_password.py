import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models import User

def reset_admin_password():
    app = create_app()
    with app.app_context():
        user = User.query.filter_by(email='alonsoencinci@gmail.com').first()
        if user:
            user.set_password('MBTaco2@25')
            db.session.commit()
            print("Password reset successfully")
        else:
            print("User not found")

if __name__ == '__main__':
    reset_admin_password() 