import os
from app import create_app, db
from init_db import init_db

app = create_app()

# Initialize database
with app.app_context():
    db.create_all()
    init_db()

if __name__ == "__main__":
    app.run() 