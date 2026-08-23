from pathlib import Path
from src.vision import tag_one_image
from src.schemas import CATEGORIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent
IMAGES_ROOT = PROJECT_ROOT / "images"

count = 0

for category in CATEGORIES:
    category_folder = IMAGES_ROOT / category
    for image_path in sorted(category_folder.glob("*.jpg")):
        count += 1
        print()
        print(image_path.name)
        print(f"Images processed: {count}")
        result = tag_one_image(str(image_path))
        print(result)
        print()