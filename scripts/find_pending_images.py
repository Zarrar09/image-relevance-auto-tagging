import asyncio
from src.database import get_connection
from src.vision import tag_one_image

MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 4
LOW_CONFIDENCE_THRESHOLD = 0.75

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
        result = None
        usage = None

        for attempt in range(1, MAX_ATTEMPTS + 1):
            try:
                result, usage = tag_one_image(image["filepath"])
                break
            except Exception as error:
                print(f"Attempt {attempt} failed for image {image['imageid']}: {error}")
                await asyncio.sleep(RETRY_DELAY_SECONDS)

        if result is None:
            await conn.execute(
                "UPDATE Images "
                "SET status = $1 "
                "WHERE imageID = $2",
                "failed",
                image["imageid"]
            )
            print(f"FAILED after {MAX_ATTEMPTS} attempts: Image ID -> {image['imageid']}")
            continue

        final_status = "done" if result.confidence >= LOW_CONFIDENCE_THRESHOLD else "flagged"

        await conn.execute(
            "UPDATE Images "
            "SET subject = $1, category = $2, attributes = $3, caption = $4, confidence = $5, status = $6 "
            "WHERE imageID = $7",
            result.subject,
            result.category,
            result.attributes,
            result.caption,
            result.confidence,
            final_status,
            image["imageid"]
        )

        await conn.execute(
            "INSERT INTO api_calls (imageID, purpose, inputTokens, outputTokens, totalTokens) "
            "VALUES ($1, $2, $3, $4, $5)",
            image["imageid"],
            "vision_tagging",
            usage["input_tokens"],
            usage["output_tokens"],
            usage["total_tokens"]
        )

        print(f"{final_status.upper()}: Image ID -> {image['imageid']} (confidence={result.confidence})")

        await asyncio.sleep(RETRY_DELAY_SECONDS)

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())