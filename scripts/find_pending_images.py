import asyncio
from src.database import get_connection
from src.vision import tag_one_image

async def main():
    conn = await get_connection()

    rows = await conn.fetch(
        "SELECT imageID, filePath "
        "FROM Images "
        "WHERE status = $1",
        "pending"
    )

    print(f"Number of pending images: {len(rows)}")

    for image in rows:
        try:
            result = tag_one_image(image["filepath"])
            updateStatus = await conn.execute(
                "UPDATE Images "
                "SET subject = $1, category = $2, attributes = $3, caption = $4, confidence = $5, status = $6 "
                "WHERE imageID = $7",
                result.subject,
                result.category,
                result.attributes,
                result.caption,
                result.confidence,
                "done",
                image["imageid"]
            )
            print(f"Passed: Image ID-> {image['imageid']}")
            print()
        except Exception as error:
            print()
            print(f"Failed: Image ID-> {image['imageid']}")
            updateStatus = await conn.execute(
                "UPDATE Images "
                "SET status = $1 "
                "WHERE imageID = $2 ",
                "failed",
                image["imageid"]
            )

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())