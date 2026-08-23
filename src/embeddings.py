import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def embed_text(text):
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=[text],
        config=types.EmbedContentConfig(output_dimensionality=768),
    )

    first_embedding = response.embeddings[0]
    numbers = first_embedding.values

    return numbers


def turn_list_into_vector_string(numbers):
    # we want a vector written like this "[0.1,0.2,0.3]"
    # so we build that string one number at a time
    pieces = []
    for number in numbers:
        pieces.append(str(number))

    joined = ",".join(pieces)
    vector_string = "[" + joined + "]"

    return vector_string