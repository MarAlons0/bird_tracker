from app.report_app import create_app
from flask_migrate import init, migrate

app = create_app()
with app.app_context():
    init()
    migrate() 