import os
from app import app, db
from init_db import init_db

# Initialize database
with app.app_context():
    db.create_all()
    init_db()

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port) 