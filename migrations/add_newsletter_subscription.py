from app import create_app, db

def upgrade():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute('ALTER TABLE users ADD COLUMN newsletter_subscription BOOLEAN DEFAULT TRUE')
            conn.commit()

def downgrade():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as conn:
            conn.execute('ALTER TABLE users DROP COLUMN newsletter_subscription')
            conn.commit() 