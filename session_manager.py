import os
import shutil
from flask import session
import logging

# Keep track of temporary files for each session
session_files = {}

def init_session(session_id):
    """Initialize a new session for temporary file tracking."""
    if session_id not in session_files:
        session_files[session_id] = {
            'processed_images': [],
            'temp_palettes': []
        }
        logging.debug(f"Initialized new session: {session_id}")

def add_processed_image(session_id, filepath):
    """Add a processed image file to the session tracking."""
    init_session(session_id)
    session_files[session_id]['processed_images'].append(filepath)
    logging.debug(f"Added processed image to session {session_id}: {filepath}")
    
    # Remove previous processed images if there are more than one
    if len(session_files[session_id]['processed_images']) > 1:
        old_image = session_files[session_id]['processed_images'].pop(0)
        try:
            if os.path.exists(old_image):
                os.remove(old_image)
                logging.debug(f"Removed old processed image: {old_image}")
        except Exception as e:
            logging.error(f"Error removing old processed image: {str(e)}")

def add_temp_palette(session_id, filepath):
    """Add a temporary palette file to the session tracking."""
    init_session(session_id)
    session_files[session_id]['temp_palettes'].append(filepath)
    logging.debug(f"Added temporary palette to session {session_id}: {filepath}")

def cleanup_session(session_id):
    """Clean up all temporary files associated with a session."""
    if session_id in session_files:
        # Remove all processed images
        for filepath in session_files[session_id]['processed_images']:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logging.debug(f"Cleaned up processed image: {filepath}")
            except Exception as e:
                logging.error(f"Error cleaning up processed image: {str(e)}")
                
        # Remove all temporary palettes
        for filepath in session_files[session_id]['temp_palettes']:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
                    logging.debug(f"Cleaned up temporary palette: {filepath}")
            except Exception as e:
                logging.error(f"Error cleaning up temporary palette: {str(e)}")
        
        # Clean up temporary palettes in the palette manager        
        try:
            from palette_manager import cleanup_session_palettes
            import config
            # Get the paths from config for this application
            app_config = config.get_config()
            palettes_dir = app_config.UPLOADED_PALETTES_DEST
            # Clean up the temporary palettes in the palette manager
            cleanup_session_palettes(session_id, palettes_dir)
        except Exception as e:
            logging.error(f"Error cleaning up palette manager: {str(e)}")
                
        # Remove the session from tracking
        del session_files[session_id]
        logging.debug(f"Cleaned up session: {session_id}")

def cleanup_all_sessions():
    """Clean up all temporary files from all sessions."""
    for session_id in list(session_files.keys()):
        cleanup_session(session_id)
    logging.debug("Cleaned up all sessions")

def cleanup_temp_directories(app_config):
    """Clean up upload and processing directories on application startup."""
    try:
        # Clean uploads directory
        uploads_dir = app_config['UPLOADED_PHOTOS_DEST']
        if os.path.exists(uploads_dir):
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error removing file {file_path}: {str(e)}")
        
        # Clean processed images directory
        processed_dir = app_config['PROCESSED_IMAGES_DEST']
        if os.path.exists(processed_dir):
            for filename in os.listdir(processed_dir):
                file_path = os.path.join(processed_dir, filename)
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                except Exception as e:
                    logging.error(f"Error removing file {file_path}: {str(e)}")
        
        # Only clean temporary palettes (not built-in ones)
        palettes_dir = app_config['UPLOADED_PALETTES_DEST']
        if os.path.exists(palettes_dir):
            for filename in os.listdir(palettes_dir):
                # Only remove files that match the temp palette pattern (contain UUID)
                if '_' in filename and filename.endswith(('.hex', '.txt')):
                    file_path = os.path.join(palettes_dir, filename)
                    try:
                        if os.path.isfile(file_path):
                            os.remove(file_path)
                    except Exception as e:
                        logging.error(f"Error removing file {file_path}: {str(e)}")
        
        logging.debug("Cleaned up all temporary directories")
    except Exception as e:
        logging.error(f"Error cleaning temporary directories: {str(e)}")