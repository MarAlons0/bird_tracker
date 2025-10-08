#!/usr/bin/env python3
"""
WSGI entry point for Render deployment
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

try:
    from app import app
    print("Successfully imported app from app.py")
except ImportError as e:
    print(f"Failed to import app: {e}")
    # Create a minimal Flask app as fallback
    from flask import Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key-for-render')
    
    @app.route('/')
    def hello():
        return '<h1>Bird Tracker App</h1><p>App is starting up...</p>'

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))