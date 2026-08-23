import os
import base64
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from src.schemas import ImageResult

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

PROMPT = """
Look at this image and identify the main animal subject.
Respond with:
- subject: a short natural description (e.g. "a red fox")
- category: exactly one of: fox, wolf, bear, deer, dog (lowercase, no other value)
- attributes: a list of 3-5 visible features (color, setting, pose)
- caption: one sentence describing the image
- confidence: your confidence in this classification, from 0.0 to 1.0
"""

def tag_one_image(image_path: str) -> ImageResult:
    image_bytes = Path(image_path).read_bytes()
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")

    interaction = client.interactions.create(
        model="gemini-3.1-flash-lite",
        input=[
            {"type": "text", "text": PROMPT},
            {"type": "image", "data": image_b64, "mime_type": "image/jpeg"},
        ],
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": ImageResult.model_json_schema(),
        },
    )

    return ImageResult.model_validate_json(interaction.output_text)