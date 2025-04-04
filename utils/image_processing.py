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

def upload_to_cloudinary(image, public_id, transformations=None):
    """Upload an image to Cloudinary."""
    # Configure Cloudinary
    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )
    
    # Convert PIL Image to bytes
    img_byte_arr = io.BytesIO()
    # Determine format from public_id extension
    format = os.path.splitext(public_id)[1][1:].upper() if os.path.splitext(public_id)[1] else 'JPEG'
    image.save(img_byte_arr, format=format)
    img_byte_arr = img_byte_arr.getvalue()
    
    # Remove extension from public_id if it exists
    public_id = os.path.splitext(public_id)[0]
    
    # Prepare upload parameters
    upload_params = {
        'public_id': public_id,
        'overwrite': True,
        'format': format.lower()
    }
    
    # Add transformations if provided
    if transformations:
        upload_params['transformation'] = transformations
    
    # Upload the image
    result = cloudinary.uploader.upload(img_byte_arr, **upload_params)
    
    current_app.logger.info(f"Successfully uploaded image to Cloudinary: {public_id}")
    return result 