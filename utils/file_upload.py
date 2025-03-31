import os
from werkzeug.utils import secure_filename
from PIL import Image

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_IMAGE_SIZE = (1920, 1080)  # Maximum dimensions for uploaded images

def allowed_file(filename):
    """Check if the file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, upload_folder):
    """Save an image file and optimize it"""
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(upload_folder, filename)
        
        # Ensure the upload folder exists
        os.makedirs(upload_folder, exist_ok=True)
        
        # Save and optimize the image
        image = Image.open(file)
        
        # Convert to RGB if necessary
        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')
        
        # Resize if larger than maximum dimensions while maintaining aspect ratio
        if image.size[0] > MAX_IMAGE_SIZE[0] or image.size[1] > MAX_IMAGE_SIZE[1]:
            image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
        
        # Save with optimization
        image.save(filepath, optimize=True, quality=85)
        
        return filename
    return None

def delete_image(filename, upload_folder):
    """Delete an image file"""
    filepath = os.path.join(upload_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False 