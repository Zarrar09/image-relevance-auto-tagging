import asyncio
from src.database import get_connection
from src.embeddings import embed_text, turn_list_into_vector_string


async def main():
    conn = await get_connection()

    images = await conn.fetch(
        "SELECT imageID, caption "
        "FROM Images "
        "WHERE status IN ('done', 'flagged') AND embedding IS NULL"
    )

    print("Images needing embeddings:", len(images))

    for image in images:
        image_id = image["imageid"]
        caption = image["caption"]

        # Turn the caption into a list of 768 numbers
        embedding_numbers = embed_text(caption)

        embedding_string = turn_list_into_vector_string(embedding_numbers)

        # Save the embedding
        await conn.execute(
            "UPDATE Images SET embedding = $1::vector WHERE imageID = $2",
            embedding_string,
            image_id
        )

        print("Embedded image ID:", image_id)

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())