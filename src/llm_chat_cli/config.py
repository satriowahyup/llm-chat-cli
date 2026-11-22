import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful and knowledgeable AI Engineering assistant. "
    "Provide concise, clear explanations with practical code examples when appropriate."
)


@dataclass(frozen=True)
class Settings:
    """Application configuration settings."""

    api_key: str
    model: str = "gemini-2.5-flash"
    temperature: float = 0.7
    max_output_tokens: int = 1024


def load_settings() -> Settings:
    """Load configuration from environment variables."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable is not set. Please define it in your .env file."
        )
    return Settings(
        api_key=api_key,
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
