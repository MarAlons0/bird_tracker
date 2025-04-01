import os
import shutil

def copy_carousel_images():
    """Copy images from birds directory to carousel directory"""
    birds_dir = os.path.join('static', 'images', 'birds')
    carousel_dir = os.path.join('static', 'images', 'carousel')
    
    # Create carousel directory if it doesn't exist
    if not os.path.exists(carousel_dir):
        os.makedirs(carousel_dir)
    
    # List of image files to copy
    images = [
        'photo1.jpg', 'photo2.jpeg', 'photo3.jpeg', 'photo4.jpeg', 'photo5.jpeg',
        'photo6.jpeg', 'photo7.jpeg', 'photo8.jpeg', 'photo9.jpeg', 'photo10.jpeg',
        'photo11.jpeg', 'photo12.jpeg', 'photo13.jpeg', 'photo14.jpg', 'photo15.jpg',
        'photo16.jpeg', 'photo17.jpeg', 'photo18.jpeg', 'photo19.jpeg', 'photo20.jpeg'
    ]
    
    # Copy each image
    for filename in images:
        src = os.path.join(birds_dir, filename)
        dst = os.path.join(carousel_dir, filename)
        if os.path.exists(src):
            shutil.copy2(src, dst)
            print(f"Copied {filename} to carousel directory")
        else:
            print(f"Warning: {filename} not found in birds directory")

if __name__ == '__main__':
    copy_carousel_images() 