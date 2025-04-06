import os
from app import app
from palette_manager import load_palettes_from_folder

def main():
    """Import palettes from the palettes folder into memory."""
    try:
        # Get the palettes directory from configuration
        palettes_dir = app.config['UPLOADED_PALETTES_DEST']
        
        # Load all palettes from the directory
        count = load_palettes_from_folder(palettes_dir)
        print(f"Successfully loaded {count} palettes from {palettes_dir}")

    except Exception as e:
        print(f"Error during palette loading: {str(e)}")

if __name__ == '__main__':
    main()