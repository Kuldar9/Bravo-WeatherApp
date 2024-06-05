# server.py
from waitress import serve
from app import app
import logging
import sys

# Set up logging for Waitress
logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger('waitress')
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

# Ensure Flask uses the same logger
app.logger.handlers = logger.handlers
app.logger.setLevel(logger.level)

if __name__ == '__main__':
    # Serve the app with Waitress
    serve(app, host='0.0.0.0', port=25565)