from flask import Flask
from flask_migrate import Migrate
from app.report_app import create_app
from app.models import db

def init_migrations():
    app = create_app()
    migrate = Migrate(app, db)
    return app, migrate

app, migrate = init_migrations()

if __name__ == '__main__':
    with app.app_context():
        from flask_migrate import upgrade as _upgrade
        print("Starting database migrations...")
        _upgrade()
        print("Database migrations completed successfully!") 