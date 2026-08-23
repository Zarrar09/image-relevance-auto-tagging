from datetime import datetime
from pydantic import BaseModel, Field
from typing import Literal

CATEGORIES = [
    "fox",
    "wolf",
    "bear",
    "deer",
    "dog"
]

class ImageResult(BaseModel):
    subject:str
    category: Literal[tuple(CATEGORIES)] # pyright: ignore[reportInvalidTypeForm]
    attributes: list[str]
    caption: str
    confidence: float = Field(ge=0, le=1)

class Image(ImageResult):
    status: Literal["pending", "processing", "done", "failed"]
    embedding: list[float] | None = None

class Post(BaseModel):
    title: str
    content: str
    expected_category: Literal[tuple(CATEGORIES)] # pyright: ignore[reportInvalidTypeForm]
    status: Literal["pending", "processing", "done", "failed"]
    embedding: list[float] | None = None