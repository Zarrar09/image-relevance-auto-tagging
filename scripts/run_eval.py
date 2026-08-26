import asyncio
import json
from pathlib import Path
from src.database import get_connection
from src.guard import rank_images_for_post, evaluate_gates

PROJECT_ROOT = Path(__file__).resolve().parent.parent
EVAL_FILE = PROJECT_ROOT / "eval_set.json"


async def main():
    conn = await get_connection()

    with open(EVAL_FILE, "r", encoding="utf-8") as f:
        eval_entries = json.load(f)

    total = 0
    top1_correct = 0
    accepted_and_correct = 0
    accepted_total = 0
    category_correct = 0

    print("post | expected image | guard top pick | distance | decision | correct? | category match?")
    print("-" * 96)

    for entry in eval_entries:
        post_id = entry["post_id"]
        correct_image_id = entry["correct_image_id"]

        post, ranked_images = await rank_images_for_post(conn, post_id, 1)
        top_image = ranked_images[0]
        top_image_id = top_image["imageid"]
        distance = top_image["distance"]

        result, explanation = evaluate_gates(post["expectedcategory"], top_image)

        is_correct = top_image_id == correct_image_id
        category_matches = top_image["category"] == post["expectedcategory"]

        total += 1
        if is_correct:
            top1_correct += 1
        if category_matches:
            category_correct += 1

        if result == "accepted":
            accepted_total += 1
            if is_correct:
                accepted_and_correct += 1

        correct_label = "yes" if is_correct else "NO"
        category_label = "yes" if category_matches else "NO"
        print(f"{post_id:>4} | {correct_image_id:>14} | {top_image_id:>14} | {distance:>8.3f} | {result:>8} | {correct_label:>3} | {category_label}")

    top1_precision = top1_correct / total
    category_precision = category_correct / total

    print()
    print(f"Posts evaluated: {total}")
    print(f"Top-1 correct: {top1_correct}")
    print(f"TOP-1 PRECISION: {top1_precision:.2%}")
    print()
    print(f"Category matches: {category_correct} / {total}")
    print(f"CATEGORY-LEVEL PRECISION: {category_precision:.2%}")
    print()

    if accepted_total > 0:
        accepted_precision = accepted_and_correct / accepted_total
        print(f"Of the {accepted_total} matches the guard accepted, {accepted_and_correct} were correct.")
        print(f"PRECISION ON ACCEPTED MATCHES: {accepted_precision:.2%}")
    else:
        print("The guard accepted no matches.")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())