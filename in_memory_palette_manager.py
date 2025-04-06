import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename

class InMemoryPalette:
    """In-memory representation of a color palette."""
    
    def __init__(self, id, name, filename, description="", is_default=False, created_at=None):
        self.id = id
        self.name = name
        self.filename = filename
        self.description = description
        self.is_default = is_default
        self.created_at = created_at or datetime.utcnow()
    
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

class InMemoryProcessedImage:
    """In-memory representation of a processed image."""
    
    def __init__(self, id, original_filename, processed_filename, palette_id, 
                 quantization_mode, max_resolution, upscale_factor=1, created_at=None):
        self.id = id
        self.original_filename = original_filename
        self.processed_filename = processed_filename
        self.palette_id = palette_id
        self.quantization_mode = quantization_mode
        self.max_resolution = max_resolution
        self.upscale_factor = upscale_factor
        self.created_at = created_at or datetime.utcnow()
        self.palette = None  # This will be set by the manager
    
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

class InMemoryPaletteManager:
    """In-memory palette and processed image manager."""
    
    def __init__(self):
        self.palettes = []
        self.processed_images = []
        self.palette_counter = 1
        self.image_counter = 1
    
    def get_all_palettes(self):
        """
        Retrieve all palettes.
        
        Returns:
            A list of InMemoryPalette objects.
        """
        return sorted(self.palettes, key=lambda p: p.name)
    
    def get_palette_by_id(self, palette_id):
        """
        Retrieve a palette by its ID.
        
        Args:
            palette_id: The ID of the palette to retrieve.
            
        Returns:
            An InMemoryPalette object or None if not found.
        """
        for palette in self.palettes:
            if str(palette.id) == str(palette_id):
                return palette
        return None
    
    def get_palette_colors(self, palette_path):
        """
        Read colors from a palette file.
        
        Args:
            palette_path: The path to the palette file.
            
        Returns:
            A list of hexadecimal color codes.
        """
        with open(palette_path, 'r') as f:
            colors = [line.strip() for line in f if line.strip()]
        return colors
    
    def add_palette(self, name, palette_file, description="", is_default=False, palettes_dir=None):
        """
        Add a new palette and save the palette file.
        
        Args:
            name: The name of the palette.
            palette_file: The uploaded palette file object.
            description: An optional description of the palette.
            is_default: Whether this palette should be set as the default.
            palettes_dir: The directory where palette files should be saved.
            
        Returns:
            The newly created InMemoryPalette object, or None if the operation failed.
        """
        try:
            # Secure the filename
            filename = secure_filename(palette_file.filename)
            
            # Create a new palette
            palette_id = self.palette_counter
            self.palette_counter += 1
            
            palette = InMemoryPalette(
                id=palette_id,
                name=name,
                filename=filename,
                description=description,
                is_default=is_default
            )
            
            # Add the palette to the list
            self.palettes.append(palette)
            
            # Save the palette file
            if palettes_dir:
                palette_file.save(os.path.join(palettes_dir, filename))
            
            return palette
        except Exception as e:
            print(f"Error adding palette: {str(e)}")
            return None
    
    def delete_palette(self, palette_id, palettes_dir=None):
        """
        Delete a palette and remove the palette file.
        
        Args:
            palette_id: The ID of the palette to delete.
            palettes_dir: The directory where palette files are stored.
            
        Returns:
            True if the operation succeeded, False otherwise.
        """
        try:
            palette = self.get_palette_by_id(palette_id)
            if not palette:
                return False
            
            # Remove the palette file
            if palettes_dir and os.path.exists(os.path.join(palettes_dir, palette.filename)):
                os.remove(os.path.join(palettes_dir, palette.filename))
            
            # Remove the palette from the list
            self.palettes = [p for p in self.palettes if p.id != palette.id]
            
            return True
        except Exception as e:
            print(f"Error deleting palette: {str(e)}")
            return False
    
    def import_default_palettes(self, palette_files, palettes_dir):
        """
        Import default palettes.
        
        Args:
            palette_files: A list of (name, path) tuples for default palettes.
            palettes_dir: The directory where palette files should be saved.
            
        Returns:
            The number of palettes successfully imported.
        """
        count = 0
        
        for name, path in palette_files:
            # Check if the palette already exists
            filename = os.path.basename(path)
            if any(p.filename == filename for p in self.palettes):
                continue
            
            # Create a new palette
            palette_id = self.palette_counter
            self.palette_counter += 1
            
            palette = InMemoryPalette(
                id=palette_id,
                name=name,
                filename=filename,
                description=f"Default {name} palette",
                is_default=True if count == 0 else False  # First palette is default
            )
            
            # Add the palette to the list
            self.palettes.append(palette)
            count += 1
        
        return count
    
    def add_processed_image(self, original_filename, processed_filename, palette_id, 
                         quantization_mode, max_resolution, upscale_factor=1):
        """
        Add a new processed image.
        
        Args:
            original_filename: The name of the original image file.
            processed_filename: The name of the processed image file.
            palette_id: The ID of the palette used to process the image.
            quantization_mode: The quantization mode used to process the image.
            max_resolution: The maximum resolution used to process the image.
            upscale_factor: The upscale factor used to process the image.
            
        Returns:
            The newly created InMemoryProcessedImage object.
        """
        image_id = self.image_counter
        self.image_counter += 1
        
        processed_image = InMemoryProcessedImage(
            id=image_id,
            original_filename=original_filename,
            processed_filename=processed_filename,
            palette_id=palette_id,
            quantization_mode=quantization_mode,
            max_resolution=max_resolution,
            upscale_factor=upscale_factor
        )
        
        # Set the palette reference
        palette = self.get_palette_by_id(palette_id)
        if palette:
            processed_image.palette = palette
        
        # Add the processed image to the list
        self.processed_images.append(processed_image)
        
        return processed_image

# Global instance for use throughout the application
palette_manager = InMemoryPaletteManager()