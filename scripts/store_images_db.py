import asyncio
from pathlib import Path
from src.database import get_connection
from src.schemas import CATEGORIES

PROJECT_ROOT = Path(__file__).resolve().parent.parent 
IMAGES = PROJECT_ROOT / "images"

async def main():
    conn = await get_connection()
    count = 0

    for category in CATEGORIES:
        each_category_path = IMAGES / category
        for image in each_category_path.iterdir():
            if image.suffix.lower() == ".jpg":
                await conn.execute(
                    "INSERT INTO images (status, filePath) VALUES ($1, $2)",
                    "pending",
                    str(image.relative_to(PROJECT_ROOT))
                )
                count += 1
            print(f"Total images stored in the database: {count}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
        


        