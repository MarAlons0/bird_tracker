#!/usr/bin/env python3
"""
WSGI entry point for Render deployment

Loads the Flask app object from the top-level app.py file explicitly,
avoiding the name conflict with the package directory `app/`.
"""
import os
import sys
import runpy

# Ensure project root is on sys.path
PROJECT_ROOT = os.path.dirname(__file__)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

APP_PY_PATH = os.path.join(PROJECT_ROOT, "app.py")

try:
    # Execute app.py as a script and retrieve the created Flask app
    module_globals = runpy.run_path(APP_PY_PATH)
    app = module_globals.get("app")
    if app is None:
        raise RuntimeError("'app' variable not found in app.py")
except Exception as e:
    # Fallback minimal Flask app with an informative message
    from flask import Flask
    app = Flask(__name__)
    error_message = str(e)
    @app.route('/')
    def _fallback():
        return f"<h1>Bird Tracker</h1><p>Startup error: {error_message}</p>"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))