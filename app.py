import os
import logging
from flask import Flask
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pixel-art-secret-key")

# Load configuration from config.py
from config import get_config
app.config.from_object(get_config())

# Create upload directories if they don't exist
os.makedirs(app.config['UPLOADED_PHOTOS_DEST'], exist_ok=True)
os.makedirs(app.config['UPLOADED_PALETTES_DEST'], exist_ok=True)
os.makedirs(app.config['PROCESSED_IMAGES_DEST'], exist_ok=True)

# Register routes
with app.app_context():
    # Import and register routes
    from routes import register_routes
    register_routes(app)
