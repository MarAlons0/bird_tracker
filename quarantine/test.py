from flask import Flask
from flask_cors import CORS
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello():
    print("Route / accessed")
    return 'Hello, World!'

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, host='localhost', port=8000) 