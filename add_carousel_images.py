import os
from app import create_app
from app.models import db, CarouselImage
import cloudinary
import cloudinary.api
import re

def get_species_name(filename):
    """Extract species name from filename and format it properly."""
    # Remove file extension and date/time pattern
    base_name = re.sub(r'_\d{8}_\d{6}', '', filename)
    base_name = os.path.splitext(base_name)[0]
    # Replace underscores with spaces and capitalize words
    species_name = ' '.join(word.capitalize() for word in base_name.split('_'))
    
    # Fix specific typos
    species_name = species_name.replace('Eagret', 'Egret')
    species_name = species_name.replace('Gho', 'Great Horned Owl')
    species_name = species_name.replace('Esgle', 'Eagle')
    
    return species_name

def get_scientific_name(species_name):
    """Get scientific name for the species."""
    scientific_names = {
        'American Crow': '(Corvus brachyrhynchos)',
        'American Goldfinch': '(Spinus tristis)',
        'American Kestrel': '(Falco sparverius)',
        'Bald Eagle': '(Haliaeetus leucocephalus)',
        'Barred Owl': '(Strix varia)',
        'Barred Owl Juvenile': '(Strix varia)',
        'Belted Kingfisher': '(Megaceryle alcyon)',
        'Blue-footed Booby': '(Sula nebouxii)',
        'Boat-tailed Grackle': '(Quiscalus major)',
        'Broad-tailed Hummingbird': '(Selasphorus platycercus)',
        'Brown Booby': '(Sula leucogaster)',
        'Brown Pelican': '(Pelecanus occidentalis)',
        'Cardinal': '(Cardinalis cardinalis)',
        'Carolina Wren': '(Thryothorus ludovicianus)',
        'Caspian Gull': '(Larus cachinnans)',
        'Cedar Waxwing': '(Bombycilla cedrorum)',
        'Chickadee': '(Poecile atricapillus)',
        'Coopers Hawk': '(Accipiter cooperii)',
        'Downy Woodpecker': '(Dryobates pubescens)',
        'Eastern Bluebird': '(Sialia sialis)',
        'Eastern Screech Owl': '(Megascops asio)',
        'Great Blue Heron': '(Ardea herodias)',
        'Great Egret': '(Ardea alba)',
        'Great Horned Owl': '(Bubo virginianus)',
        'Great-tailed Grackle': '(Quiscalus mexicanus)',
        'Green Heron': '(Butorides virescens)',
        'Indigo Bunting': '(Passerina cyanea)',
        'Mallard': '(Anas platyrhynchos)',
        'Mourning Dove': '(Zenaida macroura)',
        'Muscovy Duck': '(Cairina moschata)',
        'Osprey': '(Pandion haliaetus)',
        'Peregrine Falcon': '(Falco peregrinus)',
        'Prothonotary Warbler': '(Protonotaria citrea)',
        'Red-headed Woodpecker': '(Melanerpes erythrocephalus)',
        'Red-shouldered Hawk': '(Buteo lineatus)',
        'Red-tailed Hawk': '(Buteo jamaicensis)',
        'Rough-winged Swallow': '(Stelgidopteryx serripennis)',
        'Ruby-throated Hummingbird': '(Archilochus colubris)',
        'Ruffed Grouse': '(Bonasa umbellus)',
        'Snowy Owl': '(Bubo scandiacus)',
        'Social Flycatcher': '(Myiozetetes similis)',
        'Spruce Grouse': '(Falcipennis canadensis)',
        'Tree Swallow': '(Tachycineta bicolor)',
        'Turkey Vulture': '(Cathartes aura)',
        'Wild Turkey': '(Meleagris gallopavo)',
        'Wood Duck': '(Aix sponsa)'
    }
    return scientific_names.get(species_name, '(Scientific name unknown)')

def add_carousel_images():
    """Add carousel images to the database."""
    try:
        # List all images from Cloudinary
        resources = cloudinary.api.resources(type="upload", max_results=100)
        images = resources.get('resources', [])
        
        if not images:
            print("No images found in Cloudinary")
            return

        # First, deactivate all existing carousel images
        CarouselImage.query.update({'is_active': False})
        db.session.commit()

        # Process and add each image
        for idx, resource in enumerate(images, 1):
            filename = os.path.basename(resource['public_id'])
            species_name = get_species_name(filename)
            scientific_name = get_scientific_name(species_name)
            
            image_data = {
                'filename': filename,
                'title': species_name,
                'description': scientific_name,
                'order': idx,
                'is_active': True,
                'cloudinary_url': resource['url']
            }

            # Check if image already exists by filename
            image = CarouselImage.query.filter_by(filename=filename).first()
            if not image:
                # Create new image
                image = CarouselImage(**image_data)
                db.session.add(image)
            else:
                # Update existing image
                for key, value in image_data.items():
                    setattr(image, key, value)

        db.session.commit()
        print(f'Successfully processed {len(images)} carousel images')
        
        # Print current active carousel images
        active_images = CarouselImage.query.filter_by(is_active=True).order_by(CarouselImage.order).all()
        print('\nActive carousel images:')
        for img in active_images:
            print(f'- {img.title} {img.description} (Order: {img.order})')
            
    except Exception as e:
        print(f'Error adding carousel images: {str(e)}')
        db.session.rollback()

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        add_carousel_images() 