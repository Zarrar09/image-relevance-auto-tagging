import pytest
from pydantic import ValidationError
from src.schemas import ImageResult, CATEGORIES


def test_accepts_valid_image_result():
    data = {
        "subject": "a red fox",
        "category": "fox",
        "attributes": ["orange fur", "forest", "standing"],
        "caption": "A red fox standing in a forest",
        "confidence": 0.94,
    }
    result = ImageResult.model_validate(data)

    assert result.category == "fox"
    assert result.confidence == 0.94


def test_rejects_category_outside_the_allowed_list():
    data = {
        "subject": "a cat",
        "category": "cat",
        "attributes": ["fur"],
        "caption": "A cat",
        "confidence": 0.90,
    }
    with pytest.raises(ValidationError):
        ImageResult.model_validate(data)


def test_rejects_confidence_above_one():
    data = {
        "subject": "a red fox",
        "category": "fox",
        "attributes": ["orange fur"],
        "caption": "A red fox",
        "confidence": 1.5,
    }
    with pytest.raises(ValidationError):
        ImageResult.model_validate(data)


def test_rejects_missing_required_field():
    data = {
        "subject": "a red fox",
        "category": "fox",
        "attributes": ["orange fur"],
        "confidence": 0.90,
    }
    with pytest.raises(ValidationError):
        ImageResult.model_validate(data)


def test_rejects_malformed_json_from_model():
    bad_output = '{"subject": "a fox", "category": "fox"'

    with pytest.raises(ValidationError):
        ImageResult.model_validate_json(bad_output)


def test_every_category_in_the_list_is_accepted():
    for category in CATEGORIES:
        data = {
            "subject": "an animal",
            "category": category,
            "attributes": ["fur"],
            "caption": "An animal",
            "confidence": 0.90,
        }
        result = ImageResult.model_validate(data)
        assert result.category == category  