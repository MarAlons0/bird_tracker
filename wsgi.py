import os
from app.report_app import create_app
from init_db import init_db

app = create_app()

# Initialize database
with app.app_context():
    from app.models import db
    db.create_all()
    init_db()

if __name__ == "__main__":
    app.run() 