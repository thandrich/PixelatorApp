import os
from app import app, db
from models import Palette
from palette_manager import import_default_palettes

def main():
    """Import default palettes into the database."""
    try:
        # Clear existing default palettes
        Palette.query.filter_by(is_default=True).delete()
        db.session.commit()

        # Get all .hex files in the palettes directory
        palettes_dir = app.config['UPLOADED_PALETTES_DEST']
        palette_files = []

        for filename in os.listdir(palettes_dir):
            if filename.endswith('.hex'):
                # Create a more readable name from the filename
                name = os.path.splitext(filename)[0]
                name = name.replace('-', ' ').title()
                name = name.replace('_', ' ')

                path = os.path.join(palettes_dir, filename)

                # Verify the file is readable and contains valid hex colors
                try:
                    with open(path, 'r') as f:
                        colors = [line.strip() for line in f if line.strip()]
                    if colors:  # Only add if file contains colors
                        palette_files.append((name, path))
                except Exception as e:
                    print(f"Error reading palette file {filename}: {str(e)}")
                    continue

        # Import the palettes as default palettes
        count = import_default_palettes(palette_files, palettes_dir)
        print(f"Successfully imported {count} default palettes from {palettes_dir}")

    except Exception as e:
        print(f"Error during palette import: {str(e)}")
        db.session.rollback()

if __name__ == '__main__':
    main()