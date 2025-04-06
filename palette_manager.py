import os
import shutil
from models import Palette, db
from werkzeug.utils import secure_filename

def get_all_palettes():
    """
    Retrieve all palettes from the database.

    Returns:
        A list of Palette objects.
    """
    return Palette.query.order_by(Palette.name).all()

def get_palette_by_id(palette_id):
    """
    Retrieve a palette by its ID.

    Args:
        palette_id: The ID of the palette to retrieve.

    Returns:
        A Palette object or None if not found.
    """
    return Palette.query.get(palette_id)

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

def add_palette(name, palette_file, description="", is_default=False, palettes_dir=None):
    """
    Add a new palette to the database and save the palette file.

    Args:
        name: The name of the palette.
        palette_file: The uploaded palette file object.
        description: An optional description of the palette.
        is_default: Whether this palette should be set as the default.
        palettes_dir: The directory where palette files should be saved.

    Returns:
        The newly created Palette object, or None if the operation failed.
    """
    try:
        # Secure the filename
        filename = secure_filename(palette_file.filename)

        # Create a new palette record
        palette = Palette(
            name=name,
            filename=filename,
            description=description,
            is_default=is_default
        )

        # Add the palette to the database
        db.session.add(palette)
        db.session.commit()

        # Save the palette file
        if palettes_dir:
            palette_file.save(os.path.join(palettes_dir, filename))

        return palette
    except Exception as e:
        db.session.rollback()
        print(f"Error adding palette: {str(e)}")
        return None

def delete_palette(palette_id, palettes_dir=None):
    """
    Delete a palette from the database and remove the palette file.

    Args:
        palette_id: The ID of the palette to delete.
        palettes_dir: The directory where palette files are stored.

    Returns:
        True if the operation succeeded, False otherwise.
    """
    try:
        palette = get_palette_by_id(palette_id)
        if not palette:
            return False

        # Remove the palette file
        if palettes_dir and os.path.exists(os.path.join(palettes_dir, palette.filename)):
            os.remove(os.path.join(palettes_dir, palette.filename))

        # Remove the palette from the database
        db.session.delete(palette)
        db.session.commit()

        return True
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting palette: {str(e)}")
        return False

def import_default_palettes(palette_files, palettes_dir):
    """
    Import default palettes into the database.

    Args:
        palette_files: A list of (name, path) tuples for default palettes.
        palettes_dir: The directory where palette files should be saved.

    Returns:
        The number of palettes successfully imported.
    """
    count = 0

    for name, path in palette_files:
        filename = os.path.basename(path)

        try:
            # Create a new palette record
            palette = Palette(
                name=name,
                filename=filename,
                description=f"Default {name} palette",
                is_default=True  # All palettes from files are marked as default
            )

            # Add the palette to the database
            db.session.add(palette)
            count += 1
        except Exception as e:
            print(f"Error importing palette {name}: {str(e)}")
            continue

    try:
        db.session.commit()
    except Exception as e:
        print(f"Error committing palettes to database: {str(e)}")
        db.session.rollback()
        return 0

    return count