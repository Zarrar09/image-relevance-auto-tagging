SIMILARITY_THRESHOLD = 0.45
CONFIDENCE_THRESHOLD = 0.75


def evaluate_gates(expected_category, image_row):
    distance = image_row["distance"]
    category = image_row["category"]
    confidence = image_row["confidence"]

    if distance > SIMILARITY_THRESHOLD:
        result = "rejected"
        explanation = f"no confident match, closest image distance {distance:.3f} is above threshold {SIMILARITY_THRESHOLD}"
        return result, explanation

    if category != expected_category:
        result = "rejected"
        explanation = f"category mismatch, expected {expected_category} but detected {category}"
        return result, explanation

    if confidence < CONFIDENCE_THRESHOLD:
        result = "rejected"
        explanation = f"low confidence, image tag confidence {confidence} is below threshold {CONFIDENCE_THRESHOLD}"
        return result, explanation

    result = "accepted"
    explanation = f"confident match, {category} image matches expected category with distance {distance:.3f}"
    return result, explanation


async def rank_images_for_post(conn, post_id, limit):
    post = await conn.fetchrow(
        "SELECT postID, expectedCategory, embedding "
        "FROM Posts "
        "WHERE postID = $1",
        post_id
    )

    if post is None:
        return None, None

    ranked_images = await conn.fetch(
        "SELECT imageID, category, caption, confidence, filePath, "
        "embedding <=> $1 AS distance "
        "FROM Images "
        "WHERE embedding IS NOT NULL "
        "ORDER BY distance ASC "
        "LIMIT $2",
        post["embedding"],
        limit
    )

    return post, ranked_images


async def find_match_for_post(conn, post_id):
    post, ranked_images = await rank_images_for_post(conn, post_id, 1)

    top_image = ranked_images[0]
    distance = top_image["distance"]
    result, explanation = evaluate_gates(post["expectedcategory"], top_image)
    return top_image, distance, result, explanation


async def find_match_for_forced_image(conn, post_id, image_id):
    post = await conn.fetchrow(
        "SELECT postID, expectedCategory, embedding "
        "FROM Posts "
        "WHERE postID = $1",
        post_id
    )

    forced_image = await conn.fetchrow(
        "SELECT imageID, category, caption, confidence, "
        "embedding <=> $1 AS distance "
        "FROM Images "
        "WHERE imageID = $2",
        post["embedding"],
        image_id
    )

    distance = forced_image["distance"]
    result, explanation = evaluate_gates(post["expectedcategory"], forced_image)
    return forced_image, distance, result, explanation


async def save_match(conn, post_id, image_id, distance, result, explanation):
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