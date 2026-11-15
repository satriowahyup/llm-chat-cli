import time
from collections.abc import Iterator

from google import genai
from google.genai import errors, types

from .config import Settings

RETRYABLE_CODES = {429, 500, 503}


class ChatSession:
    def __init__(self, settings: Settings, system_prompt: str, client=None):
        self.settings = settings
        self.system_prompt = system_prompt
        self._client = client or genai.Client(api_key=settings.api_key)
        self.total_tokens = 0
        self._chat = self._new_chat()

    def _new_chat(self):
        return self._client.chats.create(
            model=self.settings.model,
            config=types.GenerateContentConfig(
                system_instruction=self.system_prompt,
                temperature=self.settings.temperature,
                max_output_tokens=self.settings.max_output_tokens,
            ),
        )

    def reset(self) -> None:
        """Kosongkan riwayat percakapan."""
        self._chat = self._new_chat()

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt
        self.reset()

    def send(self, message: str, max_retries: int = 3) -> Iterator[str]:
        """Kirim pesan dan yield potongan teks (streaming)."""
        for attempt in range(max_retries + 1):
            started = False
            try:
                last = None
                for chunk in self._chat.send_message_stream(message):
                    last = chunk
                    if chunk.text:
                        started = True
                        yield chunk.text
                if last is not None and last.usage_metadata is not None:
                    self.total_tokens += last.usage_metadata.total_token_count or 0
                return
            except errors.APIError as e:
                # Retry hanya jika error sementara dan belum ada teks yang tampil
                if e.code in RETRYABLE_CODES and not started and attempt < max_retries:
                    time.sleep(2**attempt)  # exponential backoff: 1s, 2s, 4s
                    continue
                raise