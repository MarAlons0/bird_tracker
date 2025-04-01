import os
from werkzeug.utils import secure_filename
from PIL import Image
import logging

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = (1920, 1080)  # Maximum dimensions for uploaded images

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, upload_folder):
    """Save an image file and optimize it"""
    try:
        if not file:
            logger.error("No file provided")
            return None
            
        if not allowed_file(file.filename):
            logger.error(f"Invalid file type: {file.filename}")
            return None
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        
        # Ensure the upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Log original image details
        logger.info(f"Processing image: {filename}")
        
        # Save and optimize the image
        try:
            image = Image.open(file)
            logger.info(f"Original image mode: {image.mode}, size: {image.size}")
        except Exception as e:
            logger.error(f"Error opening image: {str(e)}")
            return None
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            try:
                image = image.convert('RGB')
                logger.info("Converted image to RGB mode")
            except Exception as e:
                logger.error(f"Error converting to RGB: {str(e)}")
                return None
        
        # Resize if larger than maximum dimensions while maintaining aspect ratio
        if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
            try:
                image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                logger.info(f"Resized image to: {image.size}")
            except Exception as e:
                logger.error(f"Error resizing image: {str(e)}")
                return None
        
        # Save with optimization
        try:
            image.save(filepath, optimize=True, quality=85)
            logger.info(f"Successfully saved image to: {filepath}")
            return filename
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return None
            
    except Exception as e:
        logger.error(f"Unexpected error in save_image: {str(e)}")
        return None

def delete_image(filename, upload_folder):
    """Delete an image file"""
    try:
        filepath = os.path.join(upload_folder, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"Successfully deleted image: {filepath}")
            return True
        logger.warning(f"Image not found: {filepath}")
        return False
    except Exception as e:
        logger.error(f"Error deleting image: {str(e)}")
        return False 