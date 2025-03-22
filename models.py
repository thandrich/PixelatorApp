from datetime import datetime
from app import db

class Palette(db.Model):
    """Model for color palettes."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    filename = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_default = db.Column(db.Boolean, default=False)
    
    def __repr__(self):
        return f"<Palette {self.name}>"
        
    def to_dict(self):
        """Convert the palette to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'filename': self.filename,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_default': self.is_default
        }

class ProcessedImage(db.Model):
    """Model for tracking processed images."""
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    processed_filename = db.Column(db.String(255), nullable=False, unique=True)
    palette_id = db.Column(db.Integer, db.ForeignKey('palette.id'), nullable=False)
    quantization_mode = db.Column(db.String(50), nullable=False)
    max_resolution = db.Column(db.String(20), nullable=False)
    upscale_factor = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Define the relationship to the Palette model
    palette = db.relationship('Palette', backref=db.backref('processed_images', lazy=True))
    
    def __repr__(self):
        return f"<ProcessedImage {self.processed_filename}>"
        
    def to_dict(self):
        """Convert the processed image to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'processed_filename': self.processed_filename,
            'palette_id': self.palette_id,
            'quantization_mode': self.quantization_mode,
            'max_resolution': self.max_resolution,
            'upscale_factor': self.upscale_factor,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'palette': self.palette.name if self.palette else None
        }