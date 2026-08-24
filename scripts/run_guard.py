import asyncio
from src.database import get_connection
from src.guard import find_match_for_post, save_match


async def main():
    conn = await get_connection()

    posts = await conn.fetch("SELECT postID FROM Posts ORDER BY postID")

    for post in posts:
        post_id = post["postid"]
        top_image, distance, result, explanation = await find_match_for_post(conn, post_id)

        await save_match(conn, post_id, top_image["imageid"], distance, result, explanation)

        print(f"post {post_id}: {result} -> {explanation}")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())