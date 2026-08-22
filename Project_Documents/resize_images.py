"""
Resize all images in images/<category>/ folders so the longest side is 800px,
and re-save as JPEG at quality 85. This drastically cuts file size while
keeping enough detail for the vision model to classify correctly.

Usage:
    python resize_images.py

Expects a folder structure like:
    images/fox/*.jpg
    images/wolf/*.jpg
    images/dog/*.jpg
    images/bear/*.jpg
    images/deer/*.jpg

Overwrites the images in place. Run this ONCE before committing.
"""

import os
from pathlib import Path
from PIL import Image

MAX_DIMENSION = 800
JPEG_QUALITY = 85
IMAGES_ROOT = Path("images")
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def resize_image(filepath: Path) -> tuple[int, int]:
    """Resize one image in place. Returns (original_size, new_size) in bytes."""
    original_size = filepath.stat().st_size

    with Image.open(filepath) as img:
        # Convert to RGB in case of PNG with transparency, or other modes
        if img.mode != "RGB":
            img = img.convert("RGB")

        width, height = img.size
        if width > height:
            new_width = MAX_DIMENSION
            new_height = int(height * (MAX_DIMENSION / width))
        else:
            new_height = MAX_DIMENSION
            new_width = int(width * (MAX_DIMENSION / height))

        # Don't upscale images that are already smaller than 800px
        if width <= MAX_DIMENSION and height <= MAX_DIMENSION:
            new_width, new_height = width, height

        resized = img.resize((new_width, new_height), Image.LANCZOS)

        # Always save as .jpg regardless of original extension
        new_path = filepath.with_suffix(".jpg")
        resized.save(new_path, "JPEG", quality=JPEG_QUALITY, optimize=True)

        # If the extension changed (e.g. .png -> .jpg), remove the old file
        if new_path != filepath:
            filepath.unlink()

    new_size = new_path.stat().st_size
    return original_size, new_size


def main():
    if not IMAGES_ROOT.exists():
        print(f"Error: '{IMAGES_ROOT}' folder not found. Run this from your project root.")
        return

    total_before = 0
    total_after = 0
    count = 0

    for category_folder in sorted(IMAGES_ROOT.iterdir()):
        if not category_folder.is_dir():
            continue
        print(f"\n{category_folder.name}/")
        for filepath in sorted(category_folder.iterdir()):
            if filepath.suffix.lower() not in VALID_EXTENSIONS:
                continue
            before, after = resize_image(filepath)
            total_before += before
            total_after += after
            count += 1
            print(f"  {filepath.name}: {before/1024:.0f}KB -> {after/1024:.0f}KB")

    print(f"\n{'='*50}")
    print(f"Resized {count} images")
    print(f"Total: {total_before/1024/1024:.1f}MB -> {total_after/1024/1024:.1f}MB")


if __name__ == "__main__":
    main()