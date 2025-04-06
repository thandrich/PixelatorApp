import os
import uuid
import shutil
import logging
from werkzeug.utils import secure_filename
from flask import session

# In-memory storage for palettes
_palettes = []
# Session-based palettes (mapping session_id -> palette_ids)
_session_palettes = {}

# Function to clean up a session's palettes
def cleanup_session_palettes(session_id, palettes_dir=None):
    """
    Remove all temporary palettes associated with a session.
    This should be called when a session is cleaned up.
    
    Args:
        session_id: The ID of the session to clean up.
        palettes_dir: The directory where palette files are stored.
    """
    if session_id not in _session_palettes:
        return  # Nothing to clean up
    
    # Get all palette IDs for this session
    palette_ids = _session_palettes[session_id]
    
    # For each palette ID, remove the palette from _palettes
    # and delete the file if it exists
    palettes_to_remove = []
    
    for palette_id in palette_ids:
        # Find the palette object
        for palette in _palettes:
            if str(palette.id) == str(palette_id) and palette.is_temp:
                palettes_to_remove.append(palette)
                
                # Delete the palette file if we know where it is
                if palettes_dir and palette.filename:
                    try:
                        filepath = os.path.join(palettes_dir, palette.filename)
                        if os.path.exists(filepath):
                            os.remove(filepath)
                            logging.debug(f"Removed temporary palette file: {filepath}")
                    except Exception as e:
                        logging.error(f"Error removing palette file: {str(e)}")
    
    # Remove the palettes from the _palettes list
    for palette in palettes_to_remove:
        _palettes.remove(palette)
        logging.debug(f"Removed temporary palette: {palette.name}")
    
    # Clear the session's palette IDs
    del _session_palettes[session_id]
    logging.debug(f"Cleaned up palette session data for session: {session_id}")

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
        
        # Sort palettes by name
        _palettes.sort(key=lambda x: x.name.lower())
        
        print(f"Successfully loaded {len(_palettes)} palettes from {palettes_dir}")
        return len(_palettes)
    except Exception as e:
        print(f"Error loading palettes from folder: {str(e)}")
        return 0

def get_all_palettes():
    """
    Retrieve all palettes, filtering temporary ones based on the current session.

    Returns:
        A list of InMemoryPalette objects filtered by session if they are temporary.
    """
    # Get current session ID
    session_id = session.get('session_id')
    
    # If no session, return only permanent palettes
    if not session_id:
        return [p for p in _palettes if not p.is_temp]
    
    # Get the list of palette IDs associated with this session
    session_palette_ids = _session_palettes.get(session_id, [])
    
    # Return all permanent palettes and only temporary palettes 
    # that belong to the current session
    return [p for p in _palettes if not p.is_temp or 
            (p.is_temp and str(p.id) in session_palette_ids)]

def get_palette_by_id(palette_id):
    """
    Retrieve a palette by its ID, respecting session ownership for temporary palettes.

    Args:
        palette_id: The ID of the palette to retrieve.

    Returns:
        An InMemoryPalette object or None if not found or if the temporary palette
        doesn't belong to the current session.
    """
    # Find the palette by ID first
    found_palette = None
    for palette in _palettes:
        if str(palette.id) == str(palette_id):
            found_palette = palette
            break
            
    if not found_palette:
        return None
        
    # If it's a permanent palette, return it
    if not found_palette.is_temp:
        return found_palette
        
    # For temporary palettes, check session ownership
    session_id = session.get('session_id')
    if not session_id:
        return None  # No session, no temporary palettes
        
    # Check if this temporary palette belongs to the current session
    session_palette_ids = _session_palettes.get(session_id, [])
    if str(found_palette.id) in session_palette_ids:
        return found_palette
        
    # Temporary palette doesn't belong to this session
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
    If the palette is temporary, it is associated with the current session.

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
        
        # If it's a temporary palette, associate it with the current session
        if is_temp:
            session_id = session.get('session_id')
            if session_id:
                if session_id not in _session_palettes:
                    _session_palettes[session_id] = []
                _session_palettes[session_id].append(palette_id)
                logging.debug(f"Added palette {palette_id} to session {session_id}")
            else:
                logging.warning("Temporary palette created but no session ID found")
        
        # Save the palette file
        if palettes_dir:
            filepath = os.path.join(palettes_dir, unique_filename)
            palette_file.save(filepath)
        
        return palette
    except Exception as e:
        logging.error(f"Error adding palette: {str(e)}")
        return None