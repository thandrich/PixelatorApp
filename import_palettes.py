import os
from app import app, db
from models import Palette
from palette_manager import import_default_palettes

def main():
    """Import default palettes into the database."""
    with app.app_context():
        # Clear existing palettes if needed
        # Palette.query.delete()
        # db.session.commit()
        
        # Get all .hex files in the palettes directory
        palettes_dir = app.config['UPLOADED_PALETTES_DEST']
        palette_files = []
        
        for filename in os.listdir(palettes_dir):
            if filename.endswith('.hex'):
                name = os.path.splitext(filename)[0].replace('-', ' ').title()
                path = os.path.join(palettes_dir, filename)
                palette_files.append((name, path))
        
        # Import the palettes
        count = import_default_palettes(palette_files, palettes_dir)
        print(f"Imported {count} palettes.")

if __name__ == '__main__':
    main()