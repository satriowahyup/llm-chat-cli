import time
from collections.abc import Iterator

from google import genai
from google.genai import errors, types

from .config import Settings
from .metrics import SessionMetrics, TurnMetrics, calculate_cost

RETRYABLE_CODES = {429, 500, 503}


class ChatSession:
    """Manages an ongoing multi-turn chat session with Gemini API."""

    def __init__(self, settings: Settings, system_prompt: str, client=None):
        self.settings = settings
        self.system_prompt = system_prompt
        self._client = client or genai.Client(api_key=settings.api_key)
        self.metrics = SessionMetrics(model=settings.model)
        self.last_turn_metrics: TurnMetrics | None = None
        self.total_tokens = 0
        self.history: list[dict[str, str]] = []
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
        """Clear conversation history, reset session metrics, and create a new chat."""
        self._chat = self._new_chat()
        self.metrics.reset()
        self.last_turn_metrics = None
        self.total_tokens = 0
        self.history.clear()

    def set_system_prompt(self, prompt: str) -> None:
        """Update system instruction and reset conversation history."""
        self.system_prompt = prompt
        self.reset()

    def send(self, message: str, max_retries: int = 3) -> Iterator[str]:
        """Send message, stream response chunks, and record latency & token telemetry."""
        for attempt in range(max_retries + 1):
            started = False
            start_time = time.perf_counter()
            first_token_time = None
            accumulated_chunks: list[str] = []
            try:
                last = None
                for chunk in self._chat.send_message_stream(message):
                    last = chunk
                    if chunk.text:
                        if first_token_time is None:
                            first_token_time = time.perf_counter()
                        started = True
                        accumulated_chunks.append(chunk.text)
                        yield chunk.text

                end_time = time.perf_counter()

                # Extract tokens from usage metadata if present
                prompt_tokens = 0
                candidate_tokens = 0
                turn_total_tokens = 0
                if last is not None and last.usage_metadata is not None:
                    prompt_tokens = (
                        getattr(last.usage_metadata, "prompt_token_count", 0) or 0
                    )
                    candidate_tokens = (
                        getattr(last.usage_metadata, "candidates_token_count", 0) or 0
                    )
                    turn_total_tokens = (
                        getattr(last.usage_metadata, "total_token_count", 0) or 0
                    )

                if turn_total_tokens == 0 and (
                    prompt_tokens > 0 or candidate_tokens > 0
                ):
                    turn_total_tokens = prompt_tokens + candidate_tokens

                # Calculate telemetry and token economics
                total_duration = max(0.001, end_time - start_time)
                ttft = (
                    (first_token_time - start_time)
                    if first_token_time is not None
                    else total_duration
                )
                tokens_per_sec = (
                    candidate_tokens / total_duration if candidate_tokens > 0 else 0.0
                )
                cost = calculate_cost(
                    self.settings.model, prompt_tokens, candidate_tokens
                )

                turn = TurnMetrics(
                    prompt_tokens=prompt_tokens,
                    candidate_tokens=candidate_tokens,
                    total_tokens=turn_total_tokens,
                    time_to_first_token=ttft,
                    total_duration=total_duration,
                    tokens_per_second=tokens_per_sec,
                    estimated_cost_usd=cost,
                )
                self.last_turn_metrics = turn
                self.metrics.record_turn(turn)
                self.total_tokens = self.metrics.total_tokens

                # Record to session history
                self.history.append({"role": "user", "content": message})
                self.history.append(
                    {"role": "assistant", "content": "".join(accumulated_chunks)}
                )
                return
            except errors.APIError as e:
                # Retry only on transient errors before streaming has started
                if e.code in RETRYABLE_CODES and not started and attempt < max_retries:
                    time.sleep(2**attempt)  # exponential backoff: 1s, 2s, 4s
                    continue
                raise
