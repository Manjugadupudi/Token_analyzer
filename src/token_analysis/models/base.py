from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class ModelProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"


# ---------------------------------------------------------------------------
# Pricing table — USD per 1 million tokens.
# Update these when providers change their rates.
# ---------------------------------------------------------------------------
PRICING: dict[str, dict[str, float]] = {
    "gpt-4o":                          {"input": 2.50,  "output": 10.00},
    "gpt-4o-mini":                     {"input": 0.15,  "output":  0.60},
    "gpt-4-turbo":                     {"input": 10.00, "output": 30.00},
    "o3":                              {"input": 10.00, "output": 40.00},
    "claude-opus-4-7":                  {"input": 15.00, "output": 75.00},
    "claude-opus-4-6":                  {"input": 15.00, "output": 75.00},
    "claude-opus-4-5-20251101":         {"input": 15.00, "output": 75.00},
    "claude-sonnet-4-6":               {"input":  3.00, "output": 15.00},
    "claude-sonnet-4-5-20250929":      {"input":  3.00, "output": 15.00},
    "claude-haiku-4-5-20251001":       {"input":  0.80, "output":  4.00},
    "claude-3-5-sonnet-20241022":      {"input":  3.00, "output": 15.00},
    "grok-3":                          {"input":  3.00, "output": 15.00},
    "grok-3-mini":                     {"input":  0.30, "output":  0.50},
}

_DEFAULT_PRICING: dict[str, float] = {"input": 3.00, "output": 15.00}


def get_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """Return estimated USD cost for a single API call."""
    rates = PRICING.get(model_name, _DEFAULT_PRICING)
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1_000_000


@dataclass
class ModelResponse:
    provider: ModelProvider
    model_name: str
    prompt: str
    response_text: str
    input_tokens: int
    output_tokens: int
    total_tokens: int
    response_time_seconds: float
    cost_usd: float
    error: Optional[str] = None

    @property
    def tokens_per_second(self) -> float:
        """Output tokens generated per second."""
        if self.response_time_seconds > 0 and self.output_tokens > 0:
            return self.output_tokens / self.response_time_seconds
        return 0.0

    @property
    def success(self) -> bool:
        return self.error is None
