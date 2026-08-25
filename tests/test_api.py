from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_get_images_for_post_returns_ranked_candidates():
    response = client.get("/posts/1/images?limit=5")

    assert response.status_code == 200
    body = response.json()
    assert body["post_id"] == 1
    assert len(body["ranked_candidates"]) == 5
    assert body["result"] in ("accepted", "rejected")
    assert len(body["explanation"]) > 0


def test_ranked_candidates_are_sorted_by_distance():
    response = client.get("/posts/1/images?limit=5")
    candidates = response.json()["ranked_candidates"]

    distances = []
    for candidate in candidates:
        distances.append(candidate["distance"])

    assert distances == sorted(distances)


def test_get_images_for_missing_post_returns_404():
    response = client.get("/posts/99999/images")

    assert response.status_code == 404


def test_invalid_limit_returns_400():
    response = client.get("/posts/1/images?limit=0")

    assert response.status_code == 400


def test_non_integer_post_id_returns_422():
    response = client.get("/posts/abc/images")

    assert response.status_code == 422


def test_list_matches_returns_rows():
    response = client.get("/matches")

    assert response.status_code == 200
    assert len(response.json()) > 0


def test_list_matches_rejects_bad_review_status():
    response = client.get("/matches?review_status=banana")

    assert response.status_code == 400


def test_get_missing_match_returns_404():
    response = client.get("/matches/99999/99999")

    assert response.status_code == 404


def test_review_rejects_invalid_status_value():
    response = client.post("/matches/1/8/review", json={"review_status": "maybe"})

    assert response.status_code == 422


def test_review_approve_then_reset_to_pending():
    response = client.post("/matches/1/8/review", json={"review_status": "approved"})

    assert response.status_code == 200
    assert response.json()["review_status"] == "approved"

    filtered = client.get("/matches?review_status=approved").json()
    match_ids = []
    for match in filtered:
        match_ids.append((match["post_id"], match["image_id"]))
    assert (1, 8) in match_ids

    client.post("/matches/1/8/review", json={"review_status": "pending"})


def test_creating_the_same_match_twice_is_idempotent():
    before = client.get("/matches").json()
    client.post("/posts/1/match")
    client.post("/posts/1/match")
    after = client.get("/matches").json()

    assert len(after) == len(before)