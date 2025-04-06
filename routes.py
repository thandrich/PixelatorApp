import os
import uuid
from flask import render_template, request, jsonify, send_from_directory, url_for, redirect, flash
from werkzeug.utils import secure_filename
from app import db
from models import ProcessedImage
from image_processor import process_image
from palette_manager import get_all_palettes, get_palette_by_id, get_palette_colors, add_palette
from utils import allowed_file, parse_resolution

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
            
        # Save the uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOADED_PHOTOS_DEST'], filename)
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
            
            # Save the processed image record
            processed_image = ProcessedImage(
                original_filename=filename,
                processed_filename=processed_filename,
                palette_id=int(palette.id),  # Convert string ID to int for DB
                quantization_mode=quantization_mode,
                max_resolution=max_resolution,
                upscale_factor=upscale_factor
            )
            db.session.add(processed_image)
            db.session.commit()
            
            # Debug log for database update
            app.logger.debug(f"Saved processed image record with mode: {quantization_mode}")
            
            # Return the processed image details
            result = {
                'success': True,
                'processed_image_id': processed_image.id,
                'processed_image_url': url_for('download_file', filename=processed_filename),
                'palette_name': palette.name,
                'quantization_mode': quantization_mode  # Add this to help debug
            }
            
            app.logger.debug(f"Returning result for mode: {quantization_mode}, data: {result}")
            return jsonify(result)
        except Exception as e:
            app.logger.error(f"Error processing image with mode {quantization_mode}: {str(e)}")
            return jsonify({'error': str(e)}), 500
    
    @app.route('/download/<filename>')
    def download_file(filename):
        """Download a processed image."""
        return send_from_directory(app.config['PROCESSED_IMAGES_DEST'], filename)
    
    @app.route('/palette/<palette_id>')
    def get_palette(palette_id):
        """Get information about a specific palette."""
        palette = get_palette_by_id(palette_id)
        if not palette:
            return jsonify({'error': 'Palette not found'}), 404
            
        # Get the colors in the palette
        palette_path = os.path.join(app.config['UPLOADED_PALETTES_DEST'], palette.filename)
        colors = get_palette_colors(palette_path)
        
        return jsonify({
            'id': palette.id,
            'name': palette.name,
            'colors': colors,
            'description': palette.description
        })
    
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