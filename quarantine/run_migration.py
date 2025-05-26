from app import create_app, db

app = create_app()
with app.app_context():
    from migrations.add_newsletter_subscription import upgrade
    upgrade() 