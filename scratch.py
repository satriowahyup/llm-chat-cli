import os

from dotenv import load_dotenv
from google import genai

load_dotenv()
client = genai.Client()
response = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL"),
    contents="Jelaskan apa itu LLM dalam 2 kalimat.",
)
print(response.text)