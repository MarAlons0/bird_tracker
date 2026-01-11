"""
Main routes module - combines views and API routes.

This module maintains backward compatibility by re-exporting routes from
the split modules (views.py and api.py).

For new code, prefer importing directly from:
- app.routes.views - Page rendering routes
- app.routes.api - REST API endpoints
- app.routes.utils - Helper functions
"""
from flask import Blueprint

# Import the split blueprints
from app.routes.views import views
from app.routes.api import api

# Create a combined blueprint for backward compatibility
main = Blueprint('main', __name__)


def init_app(app):
    """Register all route blueprints with the app."""
    # Register the views blueprint (page routes)
    app.register_blueprint(views)

    # Register the API blueprint (with /api prefix)
    app.register_blueprint(api)

    return app


# Re-export for backward compatibility
from app.routes.utils import get_bird_category, ensure_user_location

__all__ = [
    'main',
    'views',
    'api',
    'init_app',
    'get_bird_category',
    'ensure_user_location',
]
