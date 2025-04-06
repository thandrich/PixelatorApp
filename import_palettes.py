import os
from app import app
from in_memory_palette_manager import palette_manager

def main():
    """Import default palettes into memory."""
    # Only import if no palettes exist
    if not palette_manager.palettes:
        
        # Get all .hex files in the palettes directory
        palettes_dir = app.config['UPLOADED_PALETTES_DEST']
        palette_files = []
        
        for filename in os.listdir(palettes_dir):
            if filename.endswith('.hex'):
                name = os.path.splitext(filename)[0].replace('-', ' ').title()
                path = os.path.join(palettes_dir, filename)
                palette_files.append((name, path))
        
        # Import the palettes
        count = palette_manager.import_default_palettes(palette_files, palettes_dir)
        print(f"Imported {count} palettes.")

if __name__ == '__main__':
    main()