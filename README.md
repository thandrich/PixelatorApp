# Pixelator App

A pixel art-style image modification web application built with Python/Flask backend and HTML/JS frontend.

## Description

Pixelator App transforms regular images into pixel art using various color palettes and quantization algorithms. Users can upload images, select from premade color palettes, and adjust settings to create unique pixel art.

## Features

- Image upload with drag-and-drop support
- Multiple color palettes (Default, Nostalgia, Resurrect-64)
- Various quantization modes:
  - Contrast: Emphasizes edges while quantizing
  - Natural: More natural color reduction using CIELAB color space
  - K-Means: Uses clustering to find dominant colors
  - K-Means (Brightness): Maps clusters based on brightness
- Adjustable resolution presets
- Pixel upscaling options

## Technology Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Frontend**: HTML, JavaScript, Bootstrap CSS
- **Image Processing**: NumPy, Scikit-image, Scikit-learn, PIL
- **Database**: PostgreSQL

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/pixelator-app.git
   cd pixelator-app
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```
   export DATABASE_URL=your_database_connection_string
   export SESSION_SECRET=your_secret_key
   ```

4. Import default palettes:
   ```
   python import_palettes.py
   ```

5. Run the application:
   ```
   python main.py
   ```

6. Open a browser and navigate to `http://localhost:5000`

## Usage

1. Upload an image using drag-and-drop or the file selector
2. Select a color palette
3. Choose quantization mode
4. Set maximum resolution and upscale factor
5. Click "Process Image" to generate pixel art
6. Download your pixelated image

## License

MIT

## Credits

- Color palettes included from various pixel art communities
- Image processing algorithms implemented based on academic research in image quantization