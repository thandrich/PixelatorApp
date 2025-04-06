import os
import uuid
from flask import render_template, request, jsonify, send_from_directory, url_for, redirect, flash, session
from werkzeug.utils import secure_filename
from app import db
from models import ProcessedImage
from image_processor import process_image
from palette_manager import get_all_palettes, get_palette_by_id, get_palette_colors, add_palette
from utils import allowed_file, parse_resolution
import session_manager

def register_routes(app):
    """Register all routes with the Flask app."""
    
    @app.route('/')
    def index():
        """Render the main application page."""
        palettes = get_all_palettes()
        
        # Get the configuration for the frontend
        quantization_modes = app.config['QUANTIZATION_MODES']
        resolution_presets = app.config['RESOLUTION_PRESETS']
        upscale_factors = app.config['UPSCALE_FACTORS']
        
        return render_template(
            'index.html',
            palettes=palettes,
            quantization_modes=quantization_modes,
            resolution_presets=resolution_presets,
            upscale_factors=upscale_factors
        )
    
    @app.route('/upload', methods=['POST'])
    def upload_file():
        """Handle image upload and processing."""
        # Check if the post request has the file part
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['file']
        
        # Check if the user did not select a file
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Check if the file is allowed
        if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
            return jsonify({'error': 'File type not allowed'}), 400
            
        # Get the parameters
        palette_id = request.form.get('palette', '1')
        quantization_mode = request.form.get('quantization_mode', app.config['DEFAULT_QUANTIZATION_MODE'])
        max_resolution = request.form.get('max_resolution', '512,512')
        upscale_factor = int(request.form.get('upscale_factor', app.config['DEFAULT_UPSCALE_FACTOR']))
        
        # Debug log for the selected quantization mode
        app.logger.debug(f"Processing with quantization mode: {quantization_mode}")
        
        # Get the palette
        palette = get_palette_by_id(palette_id)
        if not palette:
            return jsonify({'error': 'Invalid palette selected'}), 400
        
        # Generate session ID if not present
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            
        session_id = session['session_id']
            
        # Save the uploaded file to a temp location
        temp_filename = f"{str(uuid.uuid4())}.{file.filename.split('.')[-1]}"
        filepath = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], temp_filename)
        file.save(filepath)
        
        try:
            # Process the image
            palette_path = os.path.join(app.config['UPLOADED_PALETTES_DEST'], palette.filename)
            
            # Debug log for processing start
            app.logger.debug(f"Starting image processing with mode: {quantization_mode}")
            
            processed_filename = process_image(
                filepath,
                palette_path,
                app.config['PROCESSED_IMAGES_DEST'],
                max_resolution,
                quantization_mode,
                upscale_factor
            )
            
            # Debug log for processing completion
            app.logger.debug(f"Completed image processing with mode: {quantization_mode}")
            
            # Track the processed file in the session
            processed_filepath = os.path.join(app.config['PROCESSED_IMAGES_DEST'], processed_filename)
            session_manager.add_processed_image(session_id, processed_filepath)
            
            # Save a temporary record for the download
            processed_image = ProcessedImage(
                original_filename=file.filename,  # Use original filename for display
                processed_filename=processed_filename,
                palette_id=int(palette.id),
                quantization_mode=quantization_mode,
                max_resolution=max_resolution,
                upscale_factor=upscale_factor
            )
            db.session.add(processed_image)
            db.session.commit()
            
            # Debug log for database update
            app.logger.debug(f"Saved processed image record with mode: {quantization_mode}")
            
            # Remove the temporary uploaded file
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                app.logger.error(f"Error removing temporary upload: {str(e)}")
            
            # Return the processed image details
            result = {
                'success': True,
                'processed_image_id': processed_image.id,
                'processed_image_url': url_for('download_file', filename=processed_filename),
                'palette_name': palette.name,
                'quantization_mode': quantization_mode
            }
            
            app.logger.debug(f"Returning result for mode: {quantization_mode}, data: {result}")
            return jsonify(result)
        except Exception as e:
            # Cleanup the uploaded file on error
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except:
                pass
                
            app.logger.error(f"Error processing image with mode {quantization_mode}: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/download/<filename>')
    def download_file(filename):
        """Download a processed image with formatted filename."""
        # Get the processed image record from database
        processed_image = ProcessedImage.query.filter_by(processed_filename=filename).first()
        if not processed_image:
            return jsonify({'error': 'File not found'}), 404
            
        # Get original filename without extension
        original_name = os.path.splitext(processed_image.original_filename)[0]
        # Get palette name from actual palette file
        palette = get_palette_by_id(processed_image.palette_id)
        palette_name = palette.name.lower().replace(' ', '-')
        # Format the download filename
        download_filename = f"{original_name}_{palette_name}_{processed_image.quantization_mode}.png"
        
        return send_from_directory(
            app.config['PROCESSED_IMAGES_DEST'], 
            filename,
            as_attachment=True,
            download_name=download_filename
        )
    
    @app.route('/palette/<palette_id>')
    def get_palette(palette_id):
        """Get information about a specific palette."""
        palette = get_palette_by_id(palette_id)
        if not palette:
            return jsonify({'error': 'Palette not found'}), 404
            
        # Get the colors in the palette
        palette_path = os.path.join(app.config['UPLOADED_PALETTES_DEST'], palette.filename)
        
        # Safe check for palette file existence
        if not os.path.exists(palette_path):
            app.logger.error(f"Palette file not found: {palette_path}")
            return jsonify({'error': 'Palette file not found'}), 404
        
        try:
            colors = get_palette_colors(palette_path)
            
            return jsonify({
                'id': palette.id,
                'name': palette.name,
                'colors': colors,
                'description': palette.description
            })
        except Exception as e:
            app.logger.error(f"Error retrieving palette colors: {str(e)}")
            return jsonify({'error': 'Error loading palette data'}), 500
    
    @app.route('/palettes')
    def get_palettes():
        """Get all available palettes."""
        palettes = get_all_palettes()
        return jsonify([palette.to_dict() for palette in palettes])
        
    @app.route('/palette/import', methods=['POST'])
    def import_palette():
        """Import a custom palette."""
        # Check if the post request has the file part
        if 'palette_file' not in request.files:
            return jsonify({'error': 'No file part'}), 400
            
        file = request.files['palette_file']
        
        # Check if the user did not select a file
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Check if file has a valid extension (.hex or .txt)
        if not file.filename.endswith(('.hex', '.txt')):
            return jsonify({'error': 'Invalid file format. Please upload a .hex or .txt file.'}), 400
            
        # Generate session ID if not present
        if 'session_id' not in session:
            session['session_id'] = str(uuid.uuid4())
            
        session_id = session['session_id']
            
        # Get palette name from form or use filename without extension
        name = request.form.get('name', file.filename.rsplit('.', 1)[0])
        description = request.form.get('description', f"Custom palette: {name}")
        
        # Add the palette to the in-memory storage (marked as temporary)
        palette = add_palette(
            name=name,
            palette_file=file,
            description=description,
            is_temp=True,  # This marks it as a user-uploaded temp palette
            palettes_dir=app.config['UPLOADED_PALETTES_DEST']
        )
        
        if not palette:
            return jsonify({'error': 'Failed to import palette'}), 500
            
        # Track the palette in the user's session
        palette_path = os.path.join(app.config['UPLOADED_PALETTES_DEST'], palette.filename)
        session_manager.add_temp_palette(session_id, palette_path)
            
        # Return the imported palette details
        return jsonify({
            'id': palette.id,
            'name': palette.name,
            'description': palette.description
        })
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 errors."""
        return render_template('error.html', error=str(e), code=404), 404
    
    @app.errorhandler(500)
    def server_error(e):
        """Handle 500 errors."""
        return render_template('error.html', error=str(e), code=500), 500
        
    @app.route('/cleanup-session', methods=['POST'])
    def cleanup_user_session():
        """Clean up all temporary files associated with the current session."""
        if 'session_id' in session:
            session_id = session['session_id']
            session_manager.cleanup_session(session_id)
            # Mark the session as ready to be recreated
            session.pop('session_id', None)
            return jsonify({'success': True, 'message': 'Session cleared successfully'})
        return jsonify({'success': False, 'message': 'No active session to clean up'})