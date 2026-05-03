from __future__ import annotations

import os
import time

import anthropic

from .base import ModelProvider, ModelResponse, get_cost

# Override via environment variable to pin a different model version.
_DEFAULT_MODEL = "claude-sonnet-4-6"


async def query(prompt: str, api_key: str) -> ModelResponse:
    """Query Anthropic Claude and return a structured ModelResponse."""
    model = os.getenv("ANTHROPIC_MODEL", _DEFAULT_MODEL)
    client = anthropic.AsyncAnthropic(api_key=api_key)
    start = time.monotonic()

    try:
        message = await client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        elapsed = time.monotonic() - start
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens

        # Extract text safely from the content blocks list.
        response_text = next(
            (block.text for block in message.content if hasattr(block, "text")), ""
        )

        return ModelResponse(
            provider=ModelProvider.ANTHROPIC,
            model_name=model,
            prompt=prompt,
            response_text=response_text,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=input_tokens + output_tokens,
            response_time_seconds=elapsed,
            cost_usd=get_cost(model, input_tokens, output_tokens),
        )

    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - start
        return ModelResponse(
            provider=ModelProvider.ANTHROPIC,
            model_name=model,
            prompt=prompt,
            response_text="",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            response_time_seconds=elapsed,
            cost_usd=0.0,
            error=str(exc),
        )
