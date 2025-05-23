import os
import logging

from flask import Flask, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.utils import secure_filename

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize DeclarativeBase for SQLAlchemy
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy with the Base
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "pixel-art-secret-key")

# Load configuration from config.py
from config import get_config
app.config.from_object(get_config())

# Configure SQLAlchemy engine options
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Set an appropriate session timeout (1 day by default)
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours in seconds

# Create upload directories if they don't exist
os.makedirs(app.config['UPLOADED_PHOTOS_DEST'], exist_ok=True)
os.makedirs(app.config['UPLOADED_PALETTES_DEST'], exist_ok=True)
os.makedirs(app.config['PROCESSED_IMAGES_DEST'], exist_ok=True)

# Initialize the app with the database
db.init_app(app)

# Register routes
with app.app_context():
    # Import models and create tables
    import models
    db.create_all()
    
    # Import and register routes
    from routes import register_routes
    register_routes(app)
    
    # Load palettes from the palettes directory into memory
    from import_palettes import main as import_palettes
    import_palettes()
    
    # Import session manager
    import session_manager
    
    # Clean temporary directories on startup
    session_manager.cleanup_temp_directories(app.config)

# Register session cleanup when the app closes a request
@app.teardown_request
def cleanup_after_request(exception=None):
    """Cleanup temporary files when a session ends."""
    if 'session_id' in session and session.get('_session_expired', False):
        # Clean up only expired sessions
        session_manager.cleanup_session(session['session_id'])
        session.pop('_session_expired', None)
