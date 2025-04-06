import os
import uuid
from PIL import Image, ImageEnhance
import numpy as np
from skimage import color
from sklearn.cluster import KMeans
import logging

def hex_to_rgb(hex_color):
    """Convert a hex color string to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def downscale_image(image_path, max_resolution=(512, 512)):
    """
    Downscales an image to a maximum resolution while maintaining aspect ratio.

    Args:
        image_path: The path to the image file.
        max_resolution: A tuple representing the maximum width and height
                       of the downscaled image (default: (512, 512)).

    Returns:
        A PIL Image object representing the downscaled image.
    """
    try:
        # Open the image
        with Image.open(image_path) as img:
            # Convert to RGB if the image is in RGBA mode
            if img.mode == 'RGBA':
                img = img.convert('RGB')
                
            # Get the original dimensions
            width, height = img.size
            
            # Parse max_resolution if it's a string
            if isinstance(max_resolution, str):
                max_width, max_height = map(int, max_resolution.split(','))
            else:
                max_width, max_height = max_resolution
            
            # Calculate the scaling factor to maintain aspect ratio
            scale_width = max_width / width
            scale_height = max_height / height
            scale = min(scale_width, scale_height)
            
            # Calculate the new dimensions
            new_width = int(width * scale)
            new_height = int(height * scale)
            
            # Resize the image
            resized_img = img.resize((new_width, new_height), Image.LANCZOS)
            
            return resized_img
    except Exception as e:
        logging.error(f"Error downscaling image: {str(e)}")
        raise

def enhance_contrast(image):
    """Enhance the contrast of an image."""
    enhancer = ImageEnhance.Contrast(image)
    return enhancer.enhance(1.5)  # Increase contrast by 50%

def quantize_to_palette_cielab(image, palette_path):
    """Quantize an image to a color palette using CIELAB color space."""
    try:
        # Read the palette colors
        with open(palette_path, 'r') as f:
            palette_colors = [hex_to_rgb(line.strip()) for line in f if line.strip()]
        
        # Convert the image to a numpy array
        img_array = np.array(image)
        
        # Reshape the array to a list of pixels
        pixels = img_array.reshape(-1, 3)
        
        # Convert to CIELAB color space
        lab_pixels = color.rgb2lab(pixels / 255.0)
        lab_palette = color.rgb2lab(np.array(palette_colors) / 255.0)
        
        # For each pixel, find the closest palette color in CIELAB space
        result = np.zeros_like(pixels)
        for i, pixel in enumerate(lab_pixels):
            # Calculate the Euclidean distance to each palette color
            distances = np.sqrt(np.sum((lab_palette - pixel) ** 2, axis=1))
            # Find the index of the closest palette color
            closest_index = np.argmin(distances)
            # Use the RGB value from the palette
            result[i] = palette_colors[closest_index]
        
        # Reshape back to an image
        result = result.reshape(img_array.shape)
        
        # Create a new PIL image from the result
        return Image.fromarray(result.astype('uint8'))
    except Exception as e:
        logging.error(f"Error quantizing image with CIELAB: {str(e)}")
        raise

def quantize_with_edge_emphasis(image, palette_path):
    """Quantize an image to a color palette with edge emphasis."""
    try:
        # Enhance contrast to emphasize edges
        enhanced_img = enhance_contrast(image)
        
        # Read the palette colors
        with open(palette_path, 'r') as f:
            palette_colors = [hex_to_rgb(line.strip()) for line in f if line.strip()]
        
        # Create a flat list of RGB values for PIL
        flat_palette = [component for color in palette_colors for component in color]
        
        # Ensure the palette has 256 entries (required by PIL)
        while len(flat_palette) < 256 * 3:
            flat_palette.extend(flat_palette[:3])
        flat_palette = flat_palette[:256 * 3]
        
        # Create a new palette image
        palette_img = Image.new('P', (1, 1))
        palette_img.putpalette(flat_palette)
        
        # Convert the image to the palette
        quantized_img = enhanced_img.quantize(palette=palette_img, dither=Image.FLOYDSTEINBERG)
        
        # Convert back to RGB and return as numpy array for consistency with other modes
        rgb_img = quantized_img.convert('RGB')
        return Image.fromarray(np.array(rgb_img))
    except Exception as e:
        logging.error(f"Error quantizing image with edge emphasis: {str(e)}")
        raise

def quantize_kmeans(image, palette_path):
    """Quantizes an image using k-means clustering and closest palette color matching."""
    try:
        # Read the palette colors
        with open(palette_path, 'r') as f:
            palette_colors = [hex_to_rgb(line.strip()) for line in f if line.strip()]
        
        # Convert the image to a numpy array
        img_array = np.array(image)
        original_shape = img_array.shape
        
        # Reshape the array to a list of pixels
        pixels = img_array.reshape(-1, 3)
        
        # Apply k-means clustering
        n_colors = min(16, len(palette_colors))  # Limit to 16 colors or palette size
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get the cluster centers and labels
        cluster_centers = kmeans.cluster_centers_
        labels = kmeans.labels_
        
        # For each cluster center, find the closest palette color
        cluster_to_palette = {}
        for i, center in enumerate(cluster_centers):
            # Calculate the Euclidean distance to each palette color
            distances = np.sqrt(np.sum((np.array(palette_colors) - center) ** 2, axis=1))
            # Find the index of the closest palette color
            closest_index = np.argmin(distances)
            # Map this cluster to the palette color
            cluster_to_palette[i] = palette_colors[closest_index]
        
        # Replace each pixel with its corresponding palette color
        result = np.array([cluster_to_palette[label] for label in labels], dtype=np.uint8)
        
        # Reshape back to an image
        result = result.reshape(original_shape)
        
        # Create a new PIL image from the result
        return Image.fromarray(result)
    except Exception as e:
        logging.error(f"Error quantizing image with k-means: {str(e)}")
        raise

def quantize_kmeans_brightness(image, palette_path):
    """Quantizes an image using k-means and brightness-based palette mapping."""
    try:
        # Read the palette colors
        with open(palette_path, 'r') as f:
            palette_colors = [hex_to_rgb(line.strip()) for line in f if line.strip()]
        
        # Convert the image to a numpy array
        img_array = np.array(image)
        original_shape = img_array.shape
        
        # Reshape the array to a list of pixels
        pixels = img_array.reshape(-1, 3)
        
        # Apply k-means clustering
        n_colors = min(16, len(palette_colors))  # Limit to 16 colors or palette size
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Get the cluster centers and labels
        cluster_centers = kmeans.cluster_centers_
        labels = kmeans.labels_
        
        # Sort palette colors by brightness (luminance)
        palette_brightness = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in palette_colors]
        sorted_palette_indices = np.argsort(palette_brightness)
        sorted_palette = [palette_colors[i] for i in sorted_palette_indices]
        
        # Sort cluster centers by brightness
        cluster_brightness = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in cluster_centers]
        sorted_cluster_indices = np.argsort(cluster_brightness)
        
        # Map clusters to palette colors based on brightness order
        cluster_to_palette = {}
        for i, cluster_idx in enumerate(sorted_cluster_indices):
            # Map to a palette color with similar brightness position
            palette_idx = min(i, len(sorted_palette) - 1)
            cluster_to_palette[cluster_idx] = sorted_palette[palette_idx]
        
        # Replace each pixel with its corresponding palette color
        result = np.array([cluster_to_palette[label] for label in labels], dtype=np.uint8)
        
        # Reshape back to an image
        result = result.reshape(original_shape)
        
        # Create a new PIL image from the result
        return Image.fromarray(result)
    except Exception as e:
        logging.error(f"Error quantizing image with k-means brightness: {str(e)}")
        raise

def upscale_image(image, scale_factor):
    """Upscales an image by repeating pixels."""
    if scale_factor <= 1:
        return image
    
    try:
        # Get the original dimensions
        width, height = image.size
        
        # Calculate the new dimensions
        new_width = width * scale_factor
        new_height = height * scale_factor
        
        # Use nearest neighbor interpolation for pixel art style
        return image.resize((new_width, new_height), Image.NEAREST)
    except Exception as e:
        logging.error(f"Error upscaling image: {str(e)}")
        raise

def verify_colors(image, palette_rgb):
    """Verifies that all colors in the image are present in the palette."""
    try:
        # Convert the image to a numpy array
        img_array = np.array(image)
        
        # Get unique colors in the image
        unique_colors = np.unique(img_array.reshape(-1, 3), axis=0)
        
        # Check if each unique color is in the palette
        for color in unique_colors:
            if not any(np.array_equal(color, palette_color) for palette_color in palette_rgb):
                return False
        
        return True
    except Exception as e:
        logging.error(f"Error verifying colors: {str(e)}")
        return False

def process_image(
    image_path, 
    palette_path, 
    output_dir, 
    max_resolution=(512, 512), 
    quantization_mode="contrast", 
    upscale_factor=1
):
    """Process an image with the specified parameters and save the result."""
    try:
        # Generate a unique filename for the processed image
        filename = f"{str(uuid.uuid4())}.png"
        output_path = os.path.join(output_dir, filename)
        
        # Downscale the image
        img = downscale_image(image_path, max_resolution)
        
        # Apply the selected quantization mode
        if quantization_mode == "natural":
            img = quantize_to_palette_cielab(img, palette_path)
        elif quantization_mode == "kmeans":
            img = quantize_kmeans(img, palette_path)
        elif quantization_mode == "kmeans_brightness":
            img = quantize_kmeans_brightness(img, palette_path)
        else:  # Default to "contrast"
            img = quantize_with_edge_emphasis(img, palette_path)
        
        # Upscale the image if requested
        if upscale_factor > 1:
            img = upscale_image(img, upscale_factor)
        
        # Save the processed image
        img.save(output_path)
        
        return filename
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        raise