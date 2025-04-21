from app import create_app
from app.models import db, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    try:
        # Check if user exists
        user = User.query.filter_by(email='alonsoencinci@gmail.com').first()
        
        if not user:
            # Create user
            user = User(
                email='alonsoencinci@gmail.com',
                username='alonso',
                password_hash=generate_password_hash('user123', method='pbkdf2:sha256'),
                is_admin=False,
                is_approved=True
            )
            db.session.add(user)
            db.session.commit()
            print("User created successfully!")
        else:
            print("User already exists!")
            # Update password if needed
            user.password_hash = generate_password_hash('user123', method='pbkdf2:sha256')
            db.session.commit()
            print("Password updated!")
    except Exception as e:
        print(f"Error: {str(e)}") 