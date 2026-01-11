# This file makes the routes directory a Python package

from app.routes import main, auth, admin, views, api, utils

__all__ = ['main', 'auth', 'admin', 'views', 'api', 'utils']