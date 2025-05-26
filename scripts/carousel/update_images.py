import sys
import os
from pathlib import Path
import cloudinary
import cloudinary.api
from datetime import datetime
import random

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.parent.parent)
sys.path.append(project_root)

from app import create_app
from app.models import CarouselImage, db
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary mapping common names to scientific names
SCIENTIFIC_NAMES = {
    'American Crow': 'Corvus brachyrhynchos',
    'American Goldfinch': 'Spinus tristis',
    'American Kestrel': 'Falco sparverius',
    'Bald Eagle': 'Haliaeetus leucocephalus',
    'Barred Owl': 'Strix varia',
    'Belted Kingfisher': 'Megaceryle alcyon',
    'Blue-footed Booby': 'Sula nebouxii',
    'Boat-tailed Grackle': 'Quiscalus major',
    'Broad-tailed Hummingbird': 'Selasphorus platycercus',
    'Brown Booby': 'Sula leucogaster',
    'Brown Pelican': 'Pelecanus occidentalis',
    'Cardinal': 'Cardinalis cardinalis',
    'Carolina Wren': 'Thryothorus ludovicianus',
    'Caspian Gull': 'Larus cachinnans',
    'Cedar Waxwing': 'Bombycilla cedrorum',
    'Chickadee': 'Poecile atricapillus',
    'Cooper\'s Hawk': 'Accipiter cooperii',
    'Downy Woodpecker': 'Dryobates pubescens',
    'Eastern Bluebird': 'Sialia sialis',
    'Eastern Screech Owl': 'Megascops asio',
    'Great Blue Heron': 'Ardea herodias',
    'Great Egret': 'Ardea alba',
    'Great Horned Owl': 'Bubo virginianus',
    'Great-tailed Grackle': 'Quiscalus mexicanus',
    'Green Heron': 'Butorides virescens',
    'Indigo Bunting': 'Passerina cyanea',
    'Mallard': 'Anas platyrhynchos',
    'Mourning Dove': 'Zenaida macroura',
    'Muscovy Duck': 'Cairina moschata',
    'Osprey': 'Pandion haliaetus',
    'Peregrine Falcon': 'Falco peregrinus',
    'Prothonotary Warbler': 'Protonotaria citrea',
    'Red-headed Woodpecker': 'Melanerpes erythrocephalus',
    'Red-shouldered Hawk': 'Buteo lineatus',
    'Red-tailed Hawk': 'Buteo jamaicensis',
    'Rough-winged Swallow': 'Stelgidopteryx serripennis',
    'Ruby-throated Hummingbird': 'Archilochus colubris',
    'Ruffed Grouse': 'Bonasa umbellus',
    'Snowy Owl': 'Bubo scandiacus',
    'Social Flycatcher': 'Myiozetetes similis',
    'Spruce Grouse': 'Falcipennis canadensis',
    'Tree Swallow': 'Tachycineta bicolor',
    'Turkey Vulture': 'Cathartes aura',
    'Wild Turkey': 'Meleagris gallopavo',
    'Wood Duck': 'Aix sponsa'
}

def format_bird_name(filename):
    """Convert filename to formatted bird name."""
    # Remove timestamp and extension
    name = filename.split('_2025')[0]
    # Replace underscores with spaces
    name = name.replace('_', ' ')
    # Capitalize each word
    name = ' '.join(word.capitalize() for word in name.split())
    return name

def get_scientific_name(common_name):
    """Get scientific name for a bird."""
    return SCIENTIFIC_NAMES.get(common_name, '')

def update_carousel_images():
    """Update carousel with bird images from Cloudinary."""
    try:
        app = create_app()
        with app.app_context():
            # Configure Cloudinary
            cloudinary.config(
                cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
                api_key=os.getenv('CLOUDINARY_API_KEY'),
                api_secret=os.getenv('CLOUDINARY_API_SECRET')
            )
            
            # Get all images from Cloudinary in the carousel folder
            result = cloudinary.api.resources(
                type="upload",
                prefix="carousel/",
                max_results=100
            )
            
            # Clear existing carousel images
            CarouselImage.query.delete()
            db.session.commit()
            logger.info("Cleared existing carousel images")
            
            # Create a list of images with random order
            images_to_add = []
            for resource in result['resources']:
                # Get the filename without the carousel/ prefix
                filename = resource['public_id'].split('/')[-1]
                # Format the bird name
                bird_name = format_bird_name(filename)
                # Get scientific name
                scientific_name = get_scientific_name(bird_name)
                
                image = CarouselImage(
                    filename=filename,
                    cloudinary_url=resource['secure_url'],
                    title=bird_name,
                    description=f"({scientific_name})" if scientific_name else "",
                    order=random.randint(1, 1000),  # Random order
                    is_active=True,
                    filepath=resource['secure_url'],
                    upload_date=datetime.utcnow()
                )
                images_to_add.append(image)
                logger.info(f"Added image: {bird_name} ({scientific_name})")
            
            # Add all images to database
            for image in images_to_add:
                db.session.add(image)
            
            # Commit changes
            db.session.commit()
            logger.info(f"Successfully added {len(images_to_add)} bird images to carousel")
            
    except Exception as e:
        logger.error(f"Error updating carousel images: {str(e)}")
        raise

if __name__ == "__main__":
    update_carousel_images() 