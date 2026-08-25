from src.guard import evaluate_gates, SIMILARITY_THRESHOLD, CONFIDENCE_THRESHOLD


def test_rejects_when_distance_above_threshold():
    image_row = {"distance": 0.80, "category": "fox", "confidence": 0.95}
    result, explanation = evaluate_gates("fox", image_row)

    assert result == "rejected"
    assert "no confident match" in explanation


def test_rejects_when_category_does_not_match():
    image_row = {"distance": 0.30, "category": "wolf", "confidence": 0.95}
    result, explanation = evaluate_gates("fox", image_row)

    assert result == "rejected"
    assert "category mismatch" in explanation
    assert "expected fox" in explanation
    assert "detected wolf" in explanation


def test_rejects_when_confidence_below_threshold():
    image_row = {"distance": 0.30, "category": "fox", "confidence": 0.65}
    result, explanation = evaluate_gates("fox", image_row)

    assert result == "rejected"
    assert "low confidence" in explanation


def test_accepts_when_all_gates_pass():
    image_row = {"distance": 0.30, "category": "fox", "confidence": 0.95}
    result, explanation = evaluate_gates("fox", image_row)

    assert result == "accepted"
    assert "confident match" in explanation


def test_similarity_gate_fires_before_category_gate():
    image_row = {"distance": 0.90, "category": "wolf", "confidence": 0.20}
    result, explanation = evaluate_gates("fox", image_row)

    assert result == "rejected"
    assert "no confident match" in explanation


def test_category_gate_fires_before_confidence_gate():
    image_row = {"distance": 0.30, "category": "wolf", "confidence": 0.20}
    result, explanation = evaluate_gates("fox", image_row)

    assert result == "rejected"
    assert "category mismatch" in explanation