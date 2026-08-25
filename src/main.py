from fastapi import FastAPI, Depends, HTTPException
from src.database import get_connection
from src.guard import rank_images_for_post, evaluate_gates, save_match
from src.api_schemas import RankedImageOut, MatchDecisionOut, MatchOut, ReviewUpdate

app = FastAPI(title="Image Relevance Auto Tagging", version="1.0.0")


async def get_db():
    conn = await get_connection()
    try:
        yield conn
    finally:
        await conn.close()


def build_ranked_image(row):
    return RankedImageOut(
        image_id=row["imageid"],
        category=row["category"],
        caption=row["caption"],
        confidence=float(row["confidence"]),
        distance=float(row["distance"]),
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/posts/{post_id}/images", response_model=MatchDecisionOut)
async def get_images_for_post(post_id: int, limit: int = 5, conn=Depends(get_db)):
    if limit < 1 or limit > 50:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 50")

    post, ranked_images = await rank_images_for_post(conn, post_id, limit)

    if post is None:
        raise HTTPException(status_code=404, detail=f"post {post_id} not found")

    if len(ranked_images) == 0:
        raise HTTPException(status_code=404, detail="no embedded images available to rank")

    top_image = ranked_images[0]
    result, explanation = evaluate_gates(post["expectedcategory"], top_image)

    candidates = []
    for row in ranked_images:
        candidates.append(build_ranked_image(row))

    return MatchDecisionOut(
        post_id=post_id,
        expected_category=post["expectedcategory"],
        top_image=build_ranked_image(top_image),
        result=result,
        explanation=explanation,
        ranked_candidates=candidates,
    )


@app.post("/posts/{post_id}/match", response_model=MatchOut)
async def create_match_for_post(post_id: int, conn=Depends(get_db)):
    post, ranked_images = await rank_images_for_post(conn, post_id, 1)

    if post is None:
        raise HTTPException(status_code=404, detail=f"post {post_id} not found")

    if len(ranked_images) == 0:
        raise HTTPException(status_code=404, detail="no embedded images available to rank")

    top_image = ranked_images[0]
    distance = top_image["distance"]
    result, explanation = evaluate_gates(post["expectedcategory"], top_image)

    await save_match(conn, post_id, top_image["imageid"], distance, result, explanation)

    return MatchOut(
        post_id=post_id,
        image_id=top_image["imageid"],
        calculated_similarity=float(distance),
        result=result,
        explanation=explanation,
        review_status="pending",
    )


@app.get("/matches", response_model=list[MatchOut])
async def list_matches(review_status: str | None = None, conn=Depends(get_db)):
    if review_status is None:
        rows = await conn.fetch(
            "SELECT postID, imageID, calculatedSimilarity, result, explanation, reviewStatus "
            "FROM Matches ORDER BY postID"
        )
    else:
        if review_status not in ("pending", "approved", "rejected"):
            raise HTTPException(status_code=400, detail="review_status must be pending, approved, or rejected")
        rows = await conn.fetch(
            "SELECT postID, imageID, calculatedSimilarity, result, explanation, reviewStatus "
            "FROM Matches WHERE reviewStatus = $1 ORDER BY postID",
            review_status
        )

    matches = []
    for row in rows:
        matches.append(MatchOut(
            post_id=row["postid"],
            image_id=row["imageid"],
            calculated_similarity=float(row["calculatedsimilarity"]),
            result=row["result"],
            explanation=row["explanation"],
            review_status=row["reviewstatus"],
        ))

    return matches


@app.get("/matches/{post_id}/{image_id}", response_model=MatchOut)
async def get_match(post_id: int, image_id: int, conn=Depends(get_db)):
    row = await conn.fetchrow(
        "SELECT postID, imageID, calculatedSimilarity, result, explanation, reviewStatus "
        "FROM Matches WHERE postID = $1 AND imageID = $2",
        post_id,
        image_id
    )

    if row is None:
        raise HTTPException(status_code=404, detail=f"no match found for post {post_id} and image {image_id}")

    return MatchOut(
        post_id=row["postid"],
        image_id=row["imageid"],
        calculated_similarity=float(row["calculatedsimilarity"]),
        result=row["result"],
        explanation=row["explanation"],
        review_status=row["reviewstatus"],
    )


@app.post("/matches/{post_id}/{image_id}/review", response_model=MatchOut)
async def review_match(post_id: int, image_id: int, update: ReviewUpdate, conn=Depends(get_db)):
    row = await conn.fetchrow(
        "UPDATE Matches SET reviewStatus = $1 "
        "WHERE postID = $2 AND imageID = $3 "
        "RETURNING postID, imageID, calculatedSimilarity, result, explanation, reviewStatus",
        update.review_status,
        post_id,
        image_id
    )

    if row is None:
        raise HTTPException(status_code=404, detail=f"no match found for post {post_id} and image {image_id}")

    return MatchOut(
        post_id=row["postid"],
        image_id=row["imageid"],
        calculated_similarity=float(row["calculatedsimilarity"]),
        result=row["result"],
        explanation=row["explanation"],
        review_status=row["reviewstatus"],
    )