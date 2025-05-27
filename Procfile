web: gunicorn "app:create_app()"
scheduler: python -c "from app.scheduler import init_scheduler; init_scheduler()" 