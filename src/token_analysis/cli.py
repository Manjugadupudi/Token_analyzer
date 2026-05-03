from __future__ import annotations

import asyncio
import sys

import click
from dotenv import load_dotenv
from rich.console import Console

from . import analyzer, display, report

console = Console()


@click.command(context_settings={"help_option_names": ["-h", "--help"]})
@click.argument("prompt", required=False)
@click.option(
    "--save", "-s",
    is_flag=True,
    default=False,
    help="Append results to a CSV file for longitudinal analysis.",
)
@click.option(
    "--output", "-o",
    default="token_analysis_results.csv",
    show_default=True,
    help="CSV output file path.",
)
@click.option(
    "--models", "-m",
    multiple=True,
    type=click.Choice(["gpt", "claude", "grok"], case_sensitive=False),
    help=(
        "Models to query (repeatable flag). "
        "Defaults to all three when omitted.\n\n"
        "Example: -m gpt -m claude"
    ),
)
@click.option(
    "--interactive", "-i",
    is_flag=True,
    default=False,
    help="Start an interactive session — keep asking questions until you type 'exit'.",
)
@click.option(
    "--report", "-r",
    is_flag=True,
    default=False,
    help="Generate a self-contained HTML report and open it in the browser.",
)
@click.option(
    "--report-output",
    default="token_analysis_report.html",
    show_default=True,
    help="HTML report output file path.",
)
@click.version_option("1.0.0", prog_name="token-analysis")
def main(
    prompt: str | None,
    save: bool,
    output: str,
    models: tuple[str, ...],
    interactive: bool,
    report: bool,
    report_output: str,
) -> None:
    """
    \b
    Ask a question and compare token usage, cost, and speed across
    GPT-4o, Claude, and Grok-3 — all queried in parallel.

    \b
    Quick start
    -----------
      token-analysis "What is machine learning?"
      token-analysis --save --output results.csv
      token-analysis --report
      token-analysis -m gpt -m claude "Explain transformers in one paragraph"
      token-analysis --interactive

    \b
    API keys (set in .env or environment)
    --------------------------------------
      OPENAI_API_KEY    → GPT-4o
      ANTHROPIC_API_KEY → Claude
      XAI_API_KEY       → Grok-3
    """
    load_dotenv()
    selected = list(models) if models else ["gpt", "claude", "grok"]

    if interactive:
        _run_interactive(selected, save, output, report, report_output)
        return

    if not prompt:
        console.print()
        console.rule(
            "[bold bright_blue]Token Analysis — Multi-Model Comparison[/bold bright_blue]"
        )
        console.print()
        prompt = click.prompt(click.style("  Enter your question", fg="cyan", bold=True))

    _run_once(prompt, selected, save, output, report, report_output)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _run_once(
    prompt: str,
    selected: list[str],
    save: bool,
    output: str,
    make_report: bool = False,
    report_output: str = "token_analysis_report.html",
) -> None:
    console.print(f"\n[cyan]Querying {len(selected)} model(s) in parallel…[/cyan]")
    sys.stdout.flush()
    results = asyncio.run(analyzer.analyze(prompt, selected))

    if not results:
        console.print(
            "\n[red bold]No results obtained.[/red bold] "
            "Set at least one of: [yellow]OPENAI_API_KEY[/yellow], "
            "[yellow]ANTHROPIC_API_KEY[/yellow], [yellow]XAI_API_KEY[/yellow] "
            "in your [dim].env[/dim] file or environment.\n"
        )
        raise SystemExit(1)

    display.show_results(results, prompt)

    if save:
        display.save_to_csv(results, prompt, output)

    if make_report:
        report.generate(results, prompt, report_output, auto_open=True)


def _run_interactive(
    selected: list[str],
    save: bool,
    output: str,
    make_report: bool = False,
    report_output: str = "token_analysis_report.html",
) -> None:
    console.print()
    console.rule(
        "[bold bright_blue]Token Analysis — Interactive Mode[/bold bright_blue]"
    )
    console.print(
        "  Ask as many questions as you like. "
        "Type [bold red]exit[/bold red] or [bold red]quit[/bold red] to stop.\n"
    )

    while True:
        try:
            prompt = click.prompt(click.style("  Question", fg="cyan", bold=True))
        except (click.Abort, EOFError):
            console.print("\n[dim]Session ended.[/dim]")
            break

        if prompt.strip().lower() in {"exit", "quit", "q", ""}:
            console.print("[dim]Session ended.[/dim]")
            break

        _run_once(prompt, selected, save, output, make_report, report_output)
        console.print()


if __name__ == "__main__":
    main()
