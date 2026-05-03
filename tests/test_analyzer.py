"""Unit tests for token_analysis — no API keys required."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from token_analysis.models.base import (
    ModelProvider,
    ModelResponse,
    get_cost,
)


# ---------------------------------------------------------------------------
# Pricing / cost
# ---------------------------------------------------------------------------

def test_get_cost_known_model():
    cost = get_cost("gpt-4o", input_tokens=1_000, output_tokens=500)
    expected = (1_000 * 2.50 + 500 * 10.00) / 1_000_000
    assert abs(cost - expected) < 1e-9


def test_get_cost_unknown_model_uses_default():
    # Unknown models should fall back to the default rates, not raise.
    cost = get_cost("some-future-model-xyz", input_tokens=1_000, output_tokens=1_000)
    assert cost > 0


def test_get_cost_zero_tokens():
    assert get_cost("gpt-4o", 0, 0) == 0.0


# ---------------------------------------------------------------------------
# ModelResponse properties
# ---------------------------------------------------------------------------

def _make_response(**overrides) -> ModelResponse:
    defaults = dict(
        provider=ModelProvider.OPENAI,
        model_name="gpt-4o",
        prompt="test",
        response_text="hello world",
        input_tokens=10,
        output_tokens=100,
        total_tokens=110,
        response_time_seconds=2.0,
        cost_usd=0.001,
        error=None,
    )
    defaults.update(overrides)
    return ModelResponse(**defaults)


def test_tokens_per_second():
    r = _make_response(output_tokens=100, response_time_seconds=2.0)
    assert r.tokens_per_second == 50.0


def test_tokens_per_second_zero_time():
    r = _make_response(output_tokens=100, response_time_seconds=0.0)
    assert r.tokens_per_second == 0.0


def test_success_true_when_no_error():
    r = _make_response()
    assert r.success is True


def test_success_false_when_error():
    # Real error responses have zero token counts, matching what the model modules return.
    r = _make_response(error="API key invalid", output_tokens=0, total_tokens=0)
    assert r.success is False
    assert r.tokens_per_second == 0.0


# ---------------------------------------------------------------------------
# Analyzer — skips models whose env vars are absent
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_analyze_returns_empty_when_no_keys(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY",    raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("XAI_API_KEY",       raising=False)

    from token_analysis import analyzer
    results = await analyzer.analyze("test prompt")
    assert results == []


@pytest.mark.asyncio
async def test_analyze_calls_only_selected_models(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_response = _make_response()

    with patch("token_analysis.models.openai_model.query", new=AsyncMock(return_value=mock_response)):
        from token_analysis import analyzer
        results = await analyzer.analyze("hello", selected_models=["gpt"])

    assert len(results) == 1
    assert results[0].provider == ModelProvider.OPENAI


# ---------------------------------------------------------------------------
# Display — smoke tests (no real terminal needed)
# ---------------------------------------------------------------------------

def test_display_save_to_csv(tmp_path):
    from token_analysis.display import save_to_csv

    r = _make_response()
    output = str(tmp_path / "out.csv")
    save_to_csv([r], "test prompt", output)

    import csv
    with open(output, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    assert len(rows) == 1
    assert rows[0]["model_name"] == "gpt-4o"
    assert rows[0]["prompt"] == "test prompt"
    assert rows[0]["input_tokens"] == "10"


def test_display_save_to_csv_appends(tmp_path):
    from token_analysis.display import save_to_csv

    r = _make_response()
    output = str(tmp_path / "out.csv")
    save_to_csv([r], "first question",  output)
    save_to_csv([r], "second question", output)

    import csv
    with open(output, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    assert len(rows) == 2
