import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import User

app = create_app()

with app.app_context():
    username = 'Mario'
    password = 'admin123'
    email = 'alonsoencinci@gmail.com'
    
    user = User.query.filter_by(username=username).first()
    if user:
        print(f"User '{username}' already exists.")
    else:
        admin_user = User(
            username=username,
            is_admin=True
        )
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user '{username}' created successfully.") 