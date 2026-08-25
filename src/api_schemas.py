from pydantic import BaseModel
from typing import Literal


class RankedImageOut(BaseModel):
    image_id: int
    category: str
    caption: str
    confidence: float
    distance: float


class MatchDecisionOut(BaseModel):
    post_id: int
    expected_category: str
    top_image: RankedImageOut
    result: str
    explanation: str
    ranked_candidates: list[RankedImageOut]


class MatchOut(BaseModel):
    post_id: int
    image_id: int
    calculated_similarity: float
    result: str
    explanation: str
    review_status: str


class ReviewUpdate(BaseModel):
    review_status: Literal["approved", "rejected"]