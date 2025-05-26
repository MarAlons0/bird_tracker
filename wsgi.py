import os
import sys

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

# Import the app from the root app.py file
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run() 