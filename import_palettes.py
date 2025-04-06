import os
from app import app, db
from models import Palette
from palette_manager import import_default_palettes, get_all_palettes

def main():
    """Import default palettes into the database."""
    # Get all .hex files in the palettes directory
    palettes_dir = app.config['UPLOADED_PALETTES_DEST']
    palette_files = []
    
    # Get existing palette filenames from database
    existing_filenames = {palette.filename for palette in get_all_palettes()}
    
    # Scan the palettes directory for .hex files
    for filename in os.listdir(palettes_dir):
        if filename.endswith('.hex'):
            name = os.path.splitext(filename)[0].replace('-', ' ').title()
            path = os.path.join(palettes_dir, filename)
            
            # Only add if not already in the database
            if filename not in existing_filenames:
                palette_files.append((name, path))
    
    # Import the palettes
    if palette_files:
        count = import_default_palettes(palette_files, palettes_dir)
        print(f"Imported {count} new palettes.")
    else:
        print("No new palettes to import.")

if __name__ == '__main__':
    main()