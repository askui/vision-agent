import json
import pathlib
import uuid
from datetime import datetime
from PIL import Image

def generate_ai_element_json(image_path: pathlib.Path) -> None:
    # Open image to get dimensions
    with Image.open(image_path) as img:
        width, height = img.size

    # Create metadata
    metadata = {
        "version": 1,
        "id": str(uuid.uuid4()),
        "name": image_path.stem,
        "creationDateTime": datetime.now().isoformat(),
        "image": {
            "size": {
                "width": width,
                "height": height
            }
        }
    }

    # Write JSON file
    json_path = image_path.with_suffix('.json')
    with open(json_path, 'w') as f:
        json.dump(metadata, f, indent=2)

def main():
    fixtures_dir = pathlib.Path('tests/fixtures/images')
    for image_path in fixtures_dir.glob('*.png'):
        generate_ai_element_json(image_path)

if __name__ == '__main__':
    main()
