import asyncio
from src.database import get_connection
from src.guard import find_match_for_forced_image, SIMILARITY_THRESHOLD


async def main():
    conn = await get_connection()

    fox_post = await conn.fetchrow(
        "SELECT postID FROM Posts "
        "WHERE expectedCategory = 'fox' "
        "ORDER BY postID "
        "LIMIT 1"
    )
    fox_post_id = fox_post["postid"]

    post_row = await conn.fetchrow(
        "SELECT embedding FROM Posts WHERE postID = $1",
        fox_post_id
    )
    post_embedding = post_row["embedding"]

    wolf_image = await conn.fetchrow(
        "SELECT imageID, embedding <=> $1 AS distance "
        "FROM Images "
        "WHERE category = 'wolf' AND status = 'done' AND embedding IS NOT NULL "
        "ORDER BY distance ASC "
        "LIMIT 1",
        post_embedding
    )
    wolf_image_id = wolf_image["imageid"]

    print("PROBE 3: forcing a wolf image onto a fox post")
    print(f"fox post ID: {fox_post_id}")
    print(f"forced wolf image ID: {wolf_image_id}")
    print(f"wolf distance to fox post: {wolf_image['distance']:.3f} (similarity threshold {SIMILARITY_THRESHOLD})")
    print()

    forced_image, distance, result, explanation = await find_match_for_forced_image(
        conn, fox_post_id, wolf_image_id
    )

    print(f"RESULT: {result}")
    print(f"EXPLANATION: {explanation}")
    print()

    if result == "rejected" and "category mismatch" in explanation:
        print("PROBE 3 PASSED: the guard refused the wolf on a category mismatch.")
    elif result == "rejected":
        print("PROBE 3 rejected, but NOT on the category gate.")
        print("The wolf's distance is past the similarity threshold, so gate 1 fired first.")
    else:
        print("PROBE 3 FAILED: the guard accepted the wolf.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())