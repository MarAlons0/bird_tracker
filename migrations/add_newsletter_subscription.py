from flask_migrate import Migrate
from app import create_app, db
from models import User

def upgrade():
    app = create_app()
    with app.app_context():
        # Add newsletter_subscription column
        db.engine.execute('ALTER TABLE users ADD COLUMN newsletter_subscription BOOLEAN DEFAULT TRUE')
        db.session.commit()

def downgrade():
    app = create_app()
    with app.app_context():
        # Remove newsletter_subscription column
        db.engine.execute('ALTER TABLE users DROP COLUMN newsletter_subscription')
        db.session.commit() 