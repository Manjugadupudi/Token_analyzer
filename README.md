# Token Analysis

A command-line tool that sends the **same prompt to GPT-4o, Claude, and Grok-3 simultaneously** and gives you a side-by-side breakdown of token usage, estimated cost, response speed, and throughput — everything a data analyst needs to make informed decisions about which model to use.

---

## Features

| Capability | Detail |
|---|---|
| **Parallel queries** | All models are queried concurrently — no waiting in sequence |
| **Full responses** | Every model's answer is displayed in a rich panel |
| **Token breakdown** | Input tokens · Output tokens · Total tokens per model |
| **Cost estimate** | USD cost per call using current provider pricing |
| **Speed metrics** | Wall-clock response time and tokens/second throughput |
| **Visual bar charts** | ASCII bar charts for instant visual comparison |
| **Key insights** | Automatic identification of cheapest / fastest / most detailed model |
| **CSV export** | Append results to CSV for analysis in pandas / Excel |
| **Interactive mode** | REPL-style session — keep asking questions without re-running |
| **Model selection** | Query any subset: only GPT, only Claude + Grok, etc. |
| **Configurable models** | Override default model versions via environment variables |

---

## Demo Output

```
────────────  Token Analysis — Multi-Model Comparison  ────────────

╭─ Your Question ──────────────────────────────────────────────────╮
│ What is machine learning?                                        │
╰──────────────────────────────────────────────────────────────────╯

──────────────────────── Model Responses ──────────────────────────

╭─ gpt-4o ─────────────────────────────────────────────────────────╮
│                                                                   │
│  Machine learning is a branch of artificial intelligence that    │
│  enables computers to learn from data without being explicitly   │
│  programmed...                                                    │
│                                                                   │
╰───────────────────────────────────────────────────────────────────╯

╭─ claude-3-7-sonnet-20250219 ──────────────────────────────────────╮
│  ...                                                              │
╰───────────────────────────────────────────────────────────────────╯

╭─ grok-3 ──────────────────────────────────────────────────────────╮
│  ...                                                              │
╰───────────────────────────────────────────────────────────────────╯

────────────────────── Token Usage Analysis ───────────────────────

╭──────────────────────────────┬───────┬────────┬───────┬────────────────┬────────┬─────────╮
│ Model                        │ Input │ Output │ Total │ Est. Cost (USD)│ Time(s)│ Tok/sec │
├──────────────────────────────┼───────┼────────┼───────┼────────────────┼────────┼─────────┤
│ gpt-4o                       │    15 │    312 │   327 │   $0.003275    │   2.31 │   135.1 │
│ claude-3-7-sonnet-20250219   │    17 │    289 │   306 │   $0.004386    │   1.89 │   152.9 │
│ grok-3                       │    14 │    276 │   290 │   $0.004182    │   3.12 │    88.5 │
╰──────────────────────────────┴───────┴────────┴───────┴────────────────┴────────┴─────────╯

───────────────────────── Visual Comparison ───────────────────────

  Total Tokens
    gpt-4o                          ████████████████████████████████████  327 tokens
    claude-3-7-sonnet-20250219      █████████████████████████████████     306 tokens
    grok-3                          ███████████████████████████████       290 tokens

  Est. Cost (USD)
    gpt-4o                          ████████████████████████              $0.003275
    claude-3-7-sonnet-20250219      ████████████████████████████████████  $0.004386
    grok-3                          ██████████████████████████████████    $0.004182

  Response Time
    gpt-4o                          ██████████████████████████            2.31s
    claude-3-7-sonnet-20250219      █████████████████████                 1.89s
    grok-3                          ████████████████████████████████████  3.12s

─────────────────────────── Key Insights ──────────────────────────

  💰  Most Cost-Effective      gpt-4o                          $0.003275
  ⚡  Fastest Response         claude-3-7-sonnet-20250219      1.89s
  📝  Most Detailed            gpt-4o                          312 output tokens
  🚀  Best Throughput          claude-3-7-sonnet-20250219      152.9 tok/s
```

---

## Requirements

- Python 3.10 or higher
- At least one of:
  - OpenAI API key → [platform.openai.com](https://platform.openai.com)
  - Anthropic API key → [console.anthropic.com](https://console.anthropic.com)
  - xAI API key → [console.x.ai](https://console.x.ai)

---

## Installation

### From source (recommended for development)

```bash
# Clone the repository
git clone https://github.com/your-username/token-analysis.git
cd token-analysis

# Install in editable mode (makes the `token-analysis` command available)
pip install -e .
```

### From PyPI (once published)

```bash
pip install token-analysis
```

### With development dependencies

```bash
pip install -e ".[dev]"
```

---

## Configuration

Copy the example environment file and fill in your API keys:

```bash
cp .env.example .env
```

**.env**
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
XAI_API_KEY=xai-...
```

The tool loads `.env` automatically on startup via `python-dotenv`.  
You can also export the variables directly in your shell — either method works.

### Overriding default model versions

```
OPENAI_MODEL=gpt-4o                         # default
ANTHROPIC_MODEL=claude-3-7-sonnet-20250219  # default
XAI_MODEL=grok-3                            # default
```

---

## Usage

### Ask a single question

```bash
token-analysis "What is the difference between supervised and unsupervised learning?"
```

### Inline prompt with CSV export

```bash
token-analysis "Explain gradient descent" --save --output results.csv
```

### Query only a subset of models

```bash
token-analysis -m gpt -m claude "Summarise the transformer architecture"
```

### Interactive session (REPL mode)

```bash
token-analysis --interactive
```

Type `exit` or `quit` to end the session. All answers are saved to CSV if `--save` is set.

### Full options reference

```
Usage: token-analysis [OPTIONS] [PROMPT]

Options:
  -s, --save              Append results to a CSV file for longitudinal analysis.
  -o, --output PATH       CSV output file path.  [default: token_analysis_results.csv]
  -m, --models [gpt|claude|grok]
                          Models to query (repeatable). Defaults to all three.
  -i, --interactive       Start an interactive session.
  --version               Show version and exit.
  -h, --help              Show this message and exit.
```

---

## CSV Output Schema

Each row in the exported CSV represents one model's response to one question.

| Column | Type | Description |
|---|---|---|
| `timestamp` | ISO 8601 | When the query was made |
| `prompt` | string | The question asked |
| `provider` | string | `openai` / `anthropic` / `grok` |
| `model_name` | string | Exact model identifier |
| `input_tokens` | int | Prompt token count |
| `output_tokens` | int | Response token count |
| `total_tokens` | int | `input + output` |
| `cost_usd` | float | Estimated USD cost |
| `response_time_seconds` | float | Wall-clock latency |
| `tokens_per_second` | float | Output throughput |
| `response_preview` | string | First 300 chars of the response |
| `error` | string | Error message if the call failed |

The file is appended-to across multiple runs, making it ideal for time-series analysis.

---

## Pricing Reference

Approximate rates used for cost estimation (USD per 1 million tokens):

| Model | Input | Output |
|---|---|---|
| `gpt-4o` | $2.50 | $10.00 |
| `gpt-4o-mini` | $0.15 | $0.60 |
| `claude-3-7-sonnet-20250219` | $3.00 | $15.00 |
| `claude-3-5-sonnet-20241022` | $3.00 | $15.00 |
| `grok-3` | $3.00 | $15.00 |
| `grok-3-mini` | $0.30 | $0.50 |

> Prices change frequently. Update the `PRICING` dict in
> [src/token_analysis/models/base.py](src/token_analysis/models/base.py)
> to keep estimates accurate.

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest -v
```

Tests cover pricing logic, `ModelResponse` properties, analyzer routing, and CSV export — no API keys required.

---

## Project Structure

```
token_analysis/
├── src/
│   └── token_analysis/
│       ├── __init__.py
│       ├── cli.py                 # Click CLI entry point
│       ├── analyzer.py            # Parallel model dispatch
│       ├── display.py             # Rich terminal output + CSV export
│       └── models/
│           ├── base.py            # ModelResponse dataclass & pricing
│           ├── openai_model.py    # GPT-4o via openai SDK
│           ├── anthropic_model.py # Claude via anthropic SDK
│           └── grok_model.py      # Grok-3 via openai-compatible xAI API
├── tests/
│   └── test_analyzer.py
├── pyproject.toml
├── .env.example
└── README.md
```

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-improvement`
3. Make your changes and add tests
4. Run `pytest -v` to confirm everything passes
5. Open a pull request

---

## License

MIT — see [LICENSE](LICENSE) for details.
