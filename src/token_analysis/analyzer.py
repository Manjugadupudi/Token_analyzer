from __future__ import annotations

import asyncio
import os
from typing import List

from rich.console import Console

from .models.base import ModelResponse
from .models.anthropic_model import query as query_anthropic
from .models.grok_model import query as query_grok
from .models.openai_model import query as query_openai

_console = Console(stderr=True)


async def analyze(
    prompt: str,
    selected_models: list[str] | None = None,
) -> List[ModelResponse]:
    """
    Query all selected models concurrently and return their responses.

    Parameters
    ----------
    prompt : str
        The user question to send to every model.
    selected_models : list of {"gpt", "claude", "grok"}
        Which models to query. Defaults to all three.

    Returns
    -------
    List[ModelResponse]
        One entry per model that had an API key configured.
    """
    if selected_models is None:
        selected_models = ["gpt", "claude", "grok"]

    tasks = []

    if "gpt" in selected_models:
        key = os.getenv("OPENAI_API_KEY", "").strip()
        if key:
            tasks.append(query_openai(prompt, key))
        else:
            _console.print(
                "[yellow]⚠  OPENAI_API_KEY not set — skipping GPT-4o[/yellow]"
            )

    if "claude" in selected_models:
        key = os.getenv("ANTHROPIC_API_KEY", "").strip()
        if key:
            tasks.append(query_anthropic(prompt, key))
        else:
            _console.print(
                "[yellow]⚠  ANTHROPIC_API_KEY not set — skipping Claude[/yellow]"
            )

    if "grok" in selected_models:
        key = os.getenv("XAI_API_KEY", "").strip()
        if key:
            tasks.append(query_grok(prompt, key))
        else:
            _console.print(
                "[yellow]⚠  XAI_API_KEY not set — skipping Grok-3[/yellow]"
            )

    if not tasks:
        return []

    results = await asyncio.gather(*tasks)
    return list(results)
