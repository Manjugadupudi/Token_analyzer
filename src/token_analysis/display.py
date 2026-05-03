from __future__ import annotations

import csv
import os
from datetime import datetime
from typing import List

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from .models.base import ModelResponse, ModelProvider

console = Console(highlight=True)

# ---------------------------------------------------------------------------
# Style maps
# ---------------------------------------------------------------------------
_COLORS: dict[str, str] = {
    ModelProvider.OPENAI.value:    "bright_green",
    ModelProvider.ANTHROPIC.value: "dark_orange",
    ModelProvider.GROK.value:      "bright_cyan",
}


def _bar(value: float, max_value: float, width: int = 36) -> str:
    """Return a unicode block bar proportional to value/max_value."""
    if max_value <= 0:
        return "░" * width
    filled = max(1, round((value / max_value) * width))
    return "█" * filled + "░" * (width - filled)


# ---------------------------------------------------------------------------
# Section renderers
# ---------------------------------------------------------------------------

def show_header() -> None:
    console.print()
    console.rule(
        "[bold bright_blue]  Token Analysis — Multi-Model Comparison  [/bold bright_blue]"
    )
    console.print()


def show_prompt(prompt: str) -> None:
    console.print(
        Panel(
            f"[bold white]{prompt}[/bold white]",
            title="[cyan]Your Question[/cyan]",
            border_style="cyan",
            padding=(0, 2),
        )
    )
    console.print()


def show_responses(results: List[ModelResponse]) -> None:
    console.rule("[bold]Model Responses[/bold]")
    console.print()
    for r in results:
        color = _COLORS.get(r.provider.value, "white")
        if r.error:
            content = f"[red bold]Error:[/red bold] [red]{r.error}[/red]"
            border = "red"
            title = f"[red bold] {r.model_name} [/red bold]"
            footer = None
        else:
            content = r.response_text
            border = color
            title = f"[{color} bold] {r.model_name} [/{color} bold]"
            footer = (
                f"[dim]Tokens:[/dim]  "
                f"[cyan]in {r.input_tokens:,}[/cyan]  "
                f"[bright_green]out {r.output_tokens:,}[/bright_green]  "
                f"[yellow bold]total {r.total_tokens:,}[/yellow bold]"
                f"   [dim]·[/dim]  "
                f"[red]${r.cost_usd:.6f}[/red]"
                f"   [dim]·[/dim]  "
                f"[blue]{r.response_time_seconds:.2f}s[/blue]"
                f"   [dim]·[/dim]  "
                f"[magenta]{r.tokens_per_second:.1f} tok/s[/magenta]"
            )
        console.print(
            Panel(
                content,
                title=title,
                subtitle=footer,
                border_style=border,
                padding=(1, 2),
            )
        )
        console.print()


def show_analysis_table(results: List[ModelResponse]) -> None:
    console.rule("[bold]Token Usage Analysis[/bold]")
    console.print()

    table = Table(
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
        row_styles=["", "dim"],
        padding=(0, 1),
    )
    table.add_column("Model",          style="bold",          min_width=28)
    table.add_column("Input Tokens",   justify="right", style="cyan")
    table.add_column("Output Tokens",  justify="right", style="bright_green")
    table.add_column("Total Tokens",   justify="right", style="yellow bold")
    table.add_column("Est. Cost (USD)", justify="right", style="red")
    table.add_column("Time (s)",        justify="right", style="blue")
    table.add_column("Tok/sec",         justify="right", style="magenta")

    for r in results:
        if r.error:
            table.add_row(
                r.model_name, "—", "—", "—", "—",
                f"{r.response_time_seconds:.2f}", "—",
                style="dim red",
            )
        else:
            table.add_row(
                r.model_name,
                f"{r.input_tokens:,}",
                f"{r.output_tokens:,}",
                f"{r.total_tokens:,}",
                f"${r.cost_usd:.6f}",
                f"{r.response_time_seconds:.2f}",
                f"{r.tokens_per_second:.1f}",
            )

    console.print(table)
    console.print()


def show_visual_comparison(results: List[ModelResponse]) -> None:
    successful = [r for r in results if r.success]
    if not successful:
        return

    console.rule("[bold]Visual Comparison[/bold]")
    console.print()

    metrics: list[tuple] = [
        ("Total Tokens",   lambda r: float(r.total_tokens),           lambda v: f"{int(v):,} tokens", "yellow"),
        ("Output Tokens",  lambda r: float(r.output_tokens),          lambda v: f"{int(v):,} tokens", "bright_green"),
        ("Est. Cost (USD)", lambda r: r.cost_usd,                     lambda v: f"${v:.6f}",          "red"),
        ("Response Time",  lambda r: r.response_time_seconds,         lambda v: f"{v:.2f}s",          "blue"),
        ("Throughput",     lambda r: r.tokens_per_second,             lambda v: f"{v:.1f} tok/s",     "magenta"),
    ]

    for metric_name, getter, formatter, color in metrics:
        console.print(f"  [bold underline]{metric_name}[/bold underline]")
        values = [getter(r) for r in successful]
        max_val = max(values) if values else 1.0
        for r, val in zip(successful, values):
            bar   = _bar(val, max_val)
            label = r.model_name.ljust(30)
            console.print(
                f"    [dim]{label}[/dim]  [{color}]{bar}[/{color}]  [bold]{formatter(val)}[/bold]"
            )
        console.print()


def show_insights(results: List[ModelResponse]) -> None:
    successful = [r for r in results if r.success]
    if not successful:
        return

    console.rule("[bold]Key Insights[/bold]")
    console.print()

    cheapest       = min(successful, key=lambda r: r.cost_usd)
    fastest        = min(successful, key=lambda r: r.response_time_seconds)
    most_detailed  = max(successful, key=lambda r: r.output_tokens)
    best_throughput = max(successful, key=lambda r: r.tokens_per_second)

    rows = [
        ("Most Cost-Effective", "💰", cheapest,        f"${cheapest.cost_usd:.6f}",                    "bright_green"),
        ("Fastest Response",    "⚡", fastest,         f"{fastest.response_time_seconds:.2f}s",         "blue"),
        ("Most Detailed",       "📝", most_detailed,   f"{most_detailed.output_tokens:,} output tokens","yellow"),
        ("Best Throughput",     "🚀", best_throughput, f"{best_throughput.tokens_per_second:.1f} tok/s","magenta"),
    ]

    for label, icon, r, value, color in rows:
        console.print(
            f"  {icon}  [bold]{label:<22}[/bold]"
            f"  [{color}]{r.model_name:<30}[/{color}]"
            f"  [dim]{value}[/dim]"
        )

    console.print()


def show_results(results: List[ModelResponse], prompt: str) -> None:
    """Full display pipeline: header → prompt → responses → table → charts → insights."""
    show_header()
    show_prompt(prompt)
    show_responses(results)
    show_analysis_table(results)
    show_visual_comparison(results)
    show_insights(results)


# ---------------------------------------------------------------------------
# CSV export (append-friendly for longitudinal analysis)
# ---------------------------------------------------------------------------

def save_to_csv(results: List[ModelResponse], prompt: str, output_path: str) -> None:
    """Append this run's results to a CSV file for further analysis in Excel / pandas."""
    file_exists = os.path.exists(output_path)
    fieldnames = [
        "timestamp", "prompt",
        "provider", "model_name",
        "input_tokens", "output_tokens", "total_tokens",
        "cost_usd", "response_time_seconds", "tokens_per_second",
        "response_preview", "error",
    ]
    with open(output_path, "a", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        ts = datetime.now().isoformat()
        for r in results:
            writer.writerow({
                "timestamp":              ts,
                "prompt":                 prompt,
                "provider":               r.provider.value,
                "model_name":             r.model_name,
                "input_tokens":           r.input_tokens,
                "output_tokens":          r.output_tokens,
                "total_tokens":           r.total_tokens,
                "cost_usd":               round(r.cost_usd, 8),
                "response_time_seconds":  round(r.response_time_seconds, 3),
                "tokens_per_second":      round(r.tokens_per_second, 2),
                "response_preview":       r.response_text[:300] if r.response_text else "",
                "error":                  r.error or "",
            })

    console.print(f"\n[bright_green]✓[/bright_green] Results saved → [bold]{output_path}[/bold]")
