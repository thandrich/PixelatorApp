import os
import uuid
import shutil
from werkzeug.utils import secure_filename

# In-memory storage for palettes
_palettes = []

class InMemoryPalette:
    """An in-memory representation of a palette."""
    def __init__(self, id, name, filename, description="", is_temp=False):
        self.id = id
        self.name = name
        self.filename = filename
        self.description = description
        self.is_temp = is_temp  # True for user-uploaded palettes in session

    def to_dict(self):
        """Convert the palette to a dictionary for JSON serialization."""
        return {
            'id': self.id,
            'name': self.name,
            'filename': self.filename,
            'description': self.description,
            'is_temp': self.is_temp
        }

def load_palettes_from_folder(palettes_dir):
    """
    Load all palettes from the palettes folder.
    This should be called on application startup.
    """
    global _palettes
    _palettes = []  # Clear the palettes
    
    try:
        # Get all .hex files in the palettes directory
        palette_files = []
        
        for filename in os.listdir(palettes_dir):
            if filename.endswith('.hex'):
                # Create a more readable name from the filename
                name = os.path.splitext(filename)[0]
                name = name.replace('-', ' ').title()
                name = name.replace('_', ' ')
                
                # Add the palette to the list
                palette_id = str(len(_palettes) + 1)  # Simple ID scheme
                palette = InMemoryPalette(
                    id=palette_id,
                    name=name,
                    filename=filename,
                    description=f"{name} palette",
                    is_temp=False
                )
                _palettes.append(palette)
        
        print(f"Successfully loaded {len(_palettes)} palettes from {palettes_dir}")
        return len(_palettes)
    except Exception as e:
        print(f"Error loading palettes from folder: {str(e)}")
        return 0

def get_all_palettes():
    """
    Retrieve all palettes.

    Returns:
        A list of InMemoryPalette objects.
    """
    return _palettes

def get_palette_by_id(palette_id):
    """
    Retrieve a palette by its ID.

    Args:
        palette_id: The ID of the palette to retrieve.

    Returns:
        An InMemoryPalette object or None if not found.
    """
    for palette in _palettes:
        if str(palette.id) == str(palette_id):
            return palette
    return None

def get_palette_colors(palette_path):
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

def add_palette(name, palette_file, description="", is_temp=True, palettes_dir=None):
    """
    Add a new palette to the in-memory storage and save the palette file.

    Args:
        name: The name of the palette.
        palette_file: The uploaded palette file object.
        description: An optional description of the palette.
        is_temp: Whether this palette is temporary (user-uploaded).
        palettes_dir: The directory where palette files should be saved.

    Returns:
        The newly created InMemoryPalette object, or None if the operation failed.
    """
    try:
        # Create a unique filename to avoid conflicts
        original_filename = secure_filename(palette_file.filename)
        base, ext = os.path.splitext(original_filename)
        unique_filename = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
        
        # Generate a unique ID
        palette_id = str(len(_palettes) + 1)
        
        # Create a new palette record
        palette = InMemoryPalette(
            id=palette_id,
            name=name,
            filename=unique_filename,
            description=description,
            is_temp=is_temp
        )
        
        # Add the palette to the in-memory storage
        _palettes.append(palette)
        
        # Save the palette file
        if palettes_dir:
            filepath = os.path.join(palettes_dir, unique_filename)
            palette_file.save(filepath)
        
        return palette
    except Exception as e:
        print(f"Error adding palette: {str(e)}")
        return None