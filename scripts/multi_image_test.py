from src.vision import tag_one_image
import os
from src.schemas import CATEGORIES

folders = CATEGORIES

basePath = os.path.join(os.path.dirname(__file__), "..", "images")

allImages = []
count = 0

for i in folders:
    endpath = basePath + "\\" + i
    for image in os.listdir(endpath):
        if image.endswith(".jpg"):
            print()
            print(image)
            print(f"Images processed: {count}")
            result = tag_one_image(endpath + "\\" + image)
            count += 1
            print(result)
            print()