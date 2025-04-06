import os

class Config:
    """Base configuration class."""
    DEBUG = False
    TESTING = False
    
    # Use SQLite for development
    SQLALCHEMY_DATABASE_URI = 'sqlite:///pixel_art.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get('SESSION_SECRET', 'pixel-art-secret-key')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    UPLOADED_PHOTOS_DEST = os.path.join(os.getcwd(), 'uploads')
    UPLOADED_PALETTES_DEST = os.path.join(os.getcwd(), 'palettes')
    PROCESSED_IMAGES_DEST = os.path.join(os.getcwd(), 'processed')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    
    # Application settings
    DEFAULT_MAX_RESOLUTION = (256, 256)
    DEFAULT_QUANTIZATION_MODE = 'contrast'
    DEFAULT_UPSCALE_FACTOR = 1
    
    # Quantization modes
    QUANTIZATION_MODES = [
        {'value': 'contrast', 'name': 'Contrast', 'description': 'Emphasizes edges while quantizing'},
        {'value': 'natural', 'name': 'Natural', 'description': 'Attempts a more natural color reduction using CIELAB color space'},
        {'value': 'kmeans', 'name': 'K-Means', 'description': 'Uses k-means clustering to find dominant colors and match to palette'},
        {'value': 'kmeans_brightness', 'name': 'K-Means (Brightness)', 'description': 'Uses k-means and maps clusters based on brightness'}
    ]
    
    # Resolution presets
    RESOLUTION_PRESETS = [
        {'value': '64,64', 'name': '64 x 64'},
        {'value': '128,128', 'name': '128 x 128'},
        {'value': '256,256', 'name': '256 x 256', 'default': True},
        {'value': '512,512', 'name': '512 x 512'},
        {'value': '1024,1024', 'name': '1024 x 1024'}
    ]
    
    # Upscale factors
    UPSCALE_FACTORS = [1, 2, 4, 8, 16]

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test_pixel_art.db'

class ProductionConfig(Config):
    """Production configuration."""
    # Production-specific settings go here
    pass

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get the current configuration."""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default'])