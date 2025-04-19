from flask_migrate import Migrate
from app.report_app import create_app
from app.models import db

app = create_app()
migrate = Migrate(app, db)

if __name__ == '__main__':
    app.run() 