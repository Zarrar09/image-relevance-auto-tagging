from src.database import get_connection
from src.embeddings import embed_text, turn_list_into_vector_string

SIMILARITY_THRESHOLD = 0.45
CONFIDENCE_THRESHOLD = 0.75


async def find_match_for_post(conn, post_id):
    # get the post's expected category and its embedding
    post = await conn.fetchrow(
        "SELECT postID, expectedCategory, embedding "
        "FROM Posts "
        "WHERE postID = $1",
        post_id
    )

    # find the closest image to this post
    top_image = await conn.fetchrow(
        "SELECT imageID, category, caption, confidence, "
        "embedding <=> $1 AS distance "
        "FROM Images "
        "WHERE embedding IS NOT NULL "
        "ORDER BY distance ASC "
        "LIMIT 1",
        post["embedding"]
    )

    distance = top_image["distance"]

    # too far away to be a real match
    if distance > SIMILARITY_THRESHOLD:
        result = "rejected"
        explanation = f"no confident match, closest image distance {distance:.3f} is above threshold {SIMILARITY_THRESHOLD}"
        return top_image, distance, result, explanation

    # similar image but wrong animal
    if top_image["category"] != post["expectedcategory"]:
        result = "rejected"
        explanation = f"category mismatch, expected {post['expectedcategory']} but detected {top_image['category']}"
        return top_image, distance, result, explanation

    # the image tag itself was not reliable
    if top_image["confidence"] < CONFIDENCE_THRESHOLD:
        result = "rejected"
        explanation = f"low confidence, image tag confidence {top_image['confidence']} is below threshold {CONFIDENCE_THRESHOLD}"
        return top_image, distance, result, explanation

    # passed all checks
    result = "accepted"
    explanation = f"confident match, {top_image['category']} image matches expected category with distance {distance:.3f}"
    return top_image, distance, result, explanation


async def save_match(conn, post_id, image_id, distance, result, explanation):
    # store the guard's decision so it can be reviewed later
    await conn.execute(
        "INSERT INTO Matches (postID, imageID, calculatedSimilarity, result, explanation, reviewStatus) "
        "VALUES ($1, $2, $3, $4, $5, $6) "
        "ON CONFLICT (postID, imageID) DO UPDATE "
        "SET calculatedSimilarity = $3, result = $4, explanation = $5, reviewStatus = $6",
        post_id,
        image_id,
        distance,
        result,
        explanation,
        "pending"
    )