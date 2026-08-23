import asyncio
from src.database import get_connection
from src.embeddings import embed_text, turn_list_into_vector_string


async def main():
    conn = await get_connection()

    posts = await conn.fetch(
        "SELECT postID, postContent "
        "FROM Posts "
        "WHERE embedding IS NULL"
    )

    print("Posts needing embeddings:", len(posts))

    for post in posts:
        post_id = post["postid"]
        post_content = post["postcontent"]

        embedding_numbers = embed_text(post_content)

        embedding_string = turn_list_into_vector_string(embedding_numbers)

        await conn.execute(
            "UPDATE Posts SET embedding = $1::vector WHERE postID = $2",
            embedding_string,
            post_id
        )

        print("Embedded post ID:", post_id)

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())