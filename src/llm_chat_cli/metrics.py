from dataclasses import dataclass, field

# Official Gemini API pricing tiers per 1,000,000 (1M) tokens in USD
# Reference: Google AI Studio official pricing
PRICING_PER_1M_TOKENS = {
    # Flash models (Gemini 2.0 Flash, 2.5 Flash, 3.5 Flash)
    "flash": {
        "input": 0.075,
        "output": 0.30,
    },
    # Pro models (Gemini 1.5 Pro, 2.5 Pro)
    "pro": {
        "input": 1.25,
        "output": 5.00,
    },
    # Default fallback tier
    "default": {
        "input": 0.10,
        "output": 0.40,
    },
}


def calculate_cost(model: str, prompt_tokens: int, candidate_tokens: int) -> float:
    """Calculate estimated cost in USD based on model family and token usage."""
    model_lower = model.lower()
    if "flash" in model_lower:
        tier = PRICING_PER_1M_TOKENS["flash"]
    elif "pro" in model_lower:
        tier = PRICING_PER_1M_TOKENS["pro"]
    else:
        tier = PRICING_PER_1M_TOKENS["default"]

    input_cost = (prompt_tokens / 1_000_000) * tier["input"]
    output_cost = (candidate_tokens / 1_000_000) * tier["output"]
    return input_cost + output_cost


@dataclass
class TurnMetrics:
    """Observability metrics for a single request-response turn."""

    prompt_tokens: int = 0
    candidate_tokens: int = 0
    total_tokens: int = 0
    time_to_first_token: float = 0.0  # seconds
    total_duration: float = 0.0  # seconds
    tokens_per_second: float = 0.0
    estimated_cost_usd: float = 0.0

    @property
    def ttft_ms(self) -> float:
        """Time To First Token in milliseconds."""
        return self.time_to_first_token * 1000.0


@dataclass
class SessionMetrics:
    """Aggregated observability metrics for the entire chat session."""

    model: str = "default"
    turns: list[TurnMetrics] = field(default_factory=list)

    def record_turn(self, turn: TurnMetrics) -> None:
        """Record metrics for an individual turn."""
        self.turns.append(turn)

    def reset(self) -> None:
        """Reset all recorded turn metrics."""
        self.turns.clear()

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    @property
    def total_prompt_tokens(self) -> int:
        return sum(t.prompt_tokens for t in self.turns)

    @property
    def total_candidate_tokens(self) -> int:
        return sum(t.candidate_tokens for t in self.turns)

    @property
    def total_tokens(self) -> int:
        return sum(t.total_tokens for t in self.turns)

    @property
    def total_cost_usd(self) -> float:
        return sum(t.estimated_cost_usd for t in self.turns)

    @property
    def average_ttft_ms(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.ttft_ms for t in self.turns) / len(self.turns)

    @property
    def average_tokens_per_second(self) -> float:
        if not self.turns:
            return 0.0
        return sum(t.tokens_per_second for t in self.turns) / len(self.turns)
