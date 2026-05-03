from __future__ import annotations

import os
import time

from openai import AsyncOpenAI

from .base import ModelProvider, ModelResponse, get_cost

# xAI's API is OpenAI-compatible — just point to a different base URL.
_XAI_BASE_URL = "https://api.x.ai/v1"
_DEFAULT_MODEL = "grok-3"


async def query(prompt: str, api_key: str) -> ModelResponse:
    """Query xAI Grok-3 and return a structured ModelResponse."""
    model = os.getenv("XAI_MODEL", _DEFAULT_MODEL)
    client = AsyncOpenAI(api_key=api_key, base_url=_XAI_BASE_URL)
    start = time.monotonic()

    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )
        elapsed = time.monotonic() - start
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        total_tokens = usage.total_tokens

        return ModelResponse(
            provider=ModelProvider.GROK,
            model_name=model,
            prompt=prompt,
            response_text=response.choices[0].message.content or "",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
            response_time_seconds=elapsed,
            cost_usd=get_cost(model, input_tokens, output_tokens),
        )

    except Exception as exc:  # noqa: BLE001
        elapsed = time.monotonic() - start
        return ModelResponse(
            provider=ModelProvider.GROK,
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
