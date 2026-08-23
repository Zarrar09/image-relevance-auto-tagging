import asyncio
import json
from pathlib import Path
from src.database import get_connection

PROJECT_ROOT = Path(__file__).resolve().parent.parent
POSTS_FILE = PROJECT_ROOT / "blog_posts.json"

async def main():
    conn = await get_connection()

    with open(POSTS_FILE, "r", encoding="utf-8") as f:
        posts = json.load(f)

    count = 0
    for post in posts:
        full_content = f"{post['title']}\n\n{post['content']}"
        await conn.execute(
            "INSERT INTO Posts (postContent, expectedCategory, status) "
            "VALUES ($1, $2, $3)",
            full_content,
            post["expected_category"],
            "pending"
        )
        count += 1

    print(f"Seeded {count} posts")
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())