import os
from PIL import Image
import cloudinary
import cloudinary.uploader
from flask import current_app
from dotenv import load_dotenv
import io

# Load environment variables
load_dotenv()

def process_image(image_file):
    """Process an uploaded image file."""
    # If image_file is already a PIL Image, use it directly
    if isinstance(image_file, Image.Image):
        image = image_file
    else:
        # Open the image using PIL
        image = Image.open(image_file)
    
    # Log image information
    current_app.logger.info(f"Original image mode: {image.mode}, size: {image.size}")
    
    # Convert to RGB if needed
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Process the image here if needed (e.g., resize, optimize)
    # For now, we'll just keep the original
    
    current_app.logger.info("Successfully processed image")
    return image

def upload_to_cloudinary(image_path, folder=''):
    """Upload an image to Cloudinary.
    
    Args:
        image_path: Path to the image file or a file-like object
        folder: Optional folder name in Cloudinary
    
    Returns:
        str: The Cloudinary URL of the uploaded image
    """
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    
    try:
        # If image_path is a string (file path), read the file
        if isinstance(image_path, str):
            with open(image_path, 'rb') as f:
                img_data = f.read()
            # Use the filename as public_id
            public_id = os.path.splitext(os.path.basename(image_path))[0]
        else:
            # If it's a file-like object, read it directly
            img_data = image_path.read()
            public_id = os.path.splitext(image_path.filename)[0]
        
        # Add folder to public_id if specified
        if folder:
            public_id = f"{folder}/{public_id}"
        
        # Upload the image
        result = cloudinary.uploader.upload(
            img_data,
            public_id=public_id,
            overwrite=True
        )
        
        # Return the secure URL
        return result['secure_url']
        
    except Exception as e:
        current_app.logger.error(f"Error uploading to Cloudinary: {e}")
        raise 