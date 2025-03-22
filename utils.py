import base64
import io
from PIL import Image

def get_image_as_base64(image_path):
    """
    Convert an image file to a base64 string for display in HTML.
    
    Args:
        image_path: Path to the image file.
        
    Returns:
        A base64-encoded string representation of the image.
    """
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode("utf-8")
    except Exception as e:
        print(f"Error encoding image as base64: {str(e)}")
        return None

def pil_image_to_base64(pil_image):
    """
    Convert a PIL Image to a base64 string for display in HTML.
    
    Args:
        pil_image: A PIL Image object.
        
    Returns:
        A base64-encoded string representation of the image.
    """
    try:
        # Convert the image to bytes
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return img_str
    except Exception as e:
        print(f"Error converting PIL image to base64: {str(e)}")
        return None

def allowed_file(filename, allowed_extensions=None):
    """
    Check if a file has an allowed extension.
    
    Args:
        filename: The name of the file to check.
        allowed_extensions: A set of allowed file extensions.
        
    Returns:
        True if the file extension is allowed, False otherwise.
    """
    if allowed_extensions is None:
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def parse_resolution(resolution_str):
    """
    Parse a resolution string into a tuple of integers.
    
    Args:
        resolution_str: A string in the format 'width,height'.
        
    Returns:
        A tuple of (width, height) as integers.
    """
    try:
        width, height = map(int, resolution_str.split(','))
        return (width, height)
    except Exception as e:
        print(f"Error parsing resolution string: {str(e)}")
        return (512, 512)  # Default resolution