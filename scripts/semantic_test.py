import asyncio
from src.database import get_connection
from src.embeddings import embed_text, turn_list_into_vector_string


async def main():
    conn = await get_connection()

    # Deliberately shares no words with any fox caption or attribute,
    # to prove the system matches on meaning, not shared vocabulary.
    query_text = "Vulpes vulpes, the scientific name for a common wild canid found across the northern hemisphere."

    embedding_numbers = embed_text(query_text)
    embedding_string = turn_list_into_vector_string(embedding_numbers)

    top_images = await conn.fetch(
        "SELECT imageID, category, caption, "
        "embedding <=> $1::vector AS distance "
        "FROM Images "
        "WHERE embedding IS NOT NULL "
        "ORDER BY distance ASC "
        "LIMIT 5",
        embedding_string
    )

    print("PROBE: semantic matching without shared vocabulary")
    print(f"query text: {query_text}")
    print()
    print("top 5 closest images:")
    for row in top_images:
        print(f"  image {row['imageid']} ({row['category']}) distance={row['distance']:.3f} - {row['caption']}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())