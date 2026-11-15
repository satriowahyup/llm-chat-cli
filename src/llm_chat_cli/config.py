import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_SYSTEM_PROMPT = (
    "Kamu adalah asisten belajar AI Engineering. "
    "Jawab dalam Bahasa Indonesia, singkat dan jelas, beri contoh kode bila perlu."
)


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str = "gemini-3.5-flash"
    temperature: float = 0.7
    max_output_tokens: int = 1024


def load_settings() -> Settings:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum diset. Isi di file .env")
    return Settings(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    )