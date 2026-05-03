from __future__ import annotations

import json
import os
import webbrowser
from datetime import datetime
from typing import List

from rich.console import Console

from .models.base import ModelResponse

console = Console()

# ---------------------------------------------------------------------------
# Colour palette — matches the terminal display
# ---------------------------------------------------------------------------
_COLORS = {
    "openai":    {"border": "#22c55e", "bg": "#052e16", "badge": "#16a34a"},
    "anthropic": {"border": "#f97316", "bg": "#1c0a00", "badge": "#ea580c"},
    "grok":      {"border": "#22d3ee", "bg": "#083344", "badge": "#0891b2"},
}
_DEFAULT_COLOR = {"border": "#6366f1", "bg": "#1e1b4b", "badge": "#4f46e5"}

_CHART_COLORS = {
    "input":  "rgba(96, 165, 250, 0.85)",    # blue
    "output": "rgba(74, 222, 128, 0.85)",    # green
    "total":  "rgba(250, 204, 21, 0.85)",    # yellow
    "cost":   "rgba(248, 113, 113, 0.85)",   # red
    "time":   "rgba(129, 140, 248, 0.85)",   # indigo
    "tps":    "rgba(251, 146, 60, 0.85)",    # orange
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def generate(
    results: List[ModelResponse],
    prompt: str,
    output_path: str = "token_analysis_report.html",
    auto_open: bool = True,
) -> str:
    """Render a self-contained HTML report and optionally open it in a browser."""
    payload = _build_payload(results, prompt)
    html = _render(payload)

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(html)

    console.print(f"\n[bright_green]✓[/bright_green] HTML report saved → [bold]{output_path}[/bold]")

    if auto_open:
        webbrowser.open(f"file:///{os.path.abspath(output_path)}")

    return output_path


# ---------------------------------------------------------------------------
# Data builder
# ---------------------------------------------------------------------------

def _build_payload(results: List[ModelResponse], prompt: str) -> dict:
    models, successful = [], []
    for r in results:
        c = _COLORS.get(r.provider.value, _DEFAULT_COLOR)
        entry = {
            "model":        r.model_name,
            "provider":     r.provider.value,
            "colors":       c,
            "input":        r.input_tokens,
            "output":       r.output_tokens,
            "total":        r.total_tokens,
            "cost":         round(r.cost_usd, 8),
            "time":         round(r.response_time_seconds, 3),
            "tps":          round(r.tokens_per_second, 2),
            "response":     r.response_text,
            "error":        r.error,
        }
        models.append(entry)
        if not r.error:
            successful.append(entry)

    cheapest    = min(successful, key=lambda x: x["cost"],   default=None)
    fastest     = min(successful, key=lambda x: x["time"],   default=None)
    most_detail = max(successful, key=lambda x: x["output"], default=None)
    best_tps    = max(successful, key=lambda x: x["tps"],    default=None)

    return {
        "prompt":    prompt,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "models":    models,
        "insights": {
            "cheapest":    cheapest["model"]    if cheapest    else "—",
            "fastest":     fastest["model"]     if fastest     else "—",
            "most_detail": most_detail["model"] if most_detail else "—",
            "best_tps":    best_tps["model"]    if best_tps    else "—",
        },
    }


# ---------------------------------------------------------------------------
# HTML renderer
# ---------------------------------------------------------------------------

def _render(p: dict) -> str:
    data_json = json.dumps(p, ensure_ascii=False)
    models = p["models"]
    ins = p["insights"]

    model_labels   = json.dumps([m["model"]  for m in models])
    border_colors  = json.dumps([m["colors"]["border"] for m in models])
    input_data     = json.dumps([m["input"]  for m in models])
    output_data    = json.dumps([m["output"] for m in models])
    total_data     = json.dumps([m["total"]  for m in models])
    cost_data      = json.dumps([m["cost"]   for m in models])
    time_data      = json.dumps([m["time"]   for m in models])
    tps_data       = json.dumps([m["tps"]    for m in models])

    # ── Response cards ──
    cards_html = ""
    for m in models:
        c = m["colors"]
        if m["error"]:
            body = f'<p class="error-msg">⚠ {m["error"]}</p>'
            footer = ""
        else:
            escaped = m["response"].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            body = f'<pre class="response-text">{escaped}</pre>'
            footer = f"""
            <div class="card-footer">
              <span class="badge badge-in">in {m['input']:,}</span>
              <span class="badge badge-out">out {m['output']:,}</span>
              <span class="badge badge-total">total {m['total']:,}</span>
              <span class="badge badge-cost">${m['cost']:.6f}</span>
              <span class="badge badge-time">{m['time']:.2f}s</span>
              <span class="badge badge-tps">{m['tps']:.1f} tok/s</span>
            </div>"""

        cards_html += f"""
        <div class="response-card" style="border-color:{c['border']};background:{c['bg']};">
          <div class="card-header" style="background:{c['border']}20;border-bottom:1px solid {c['border']}40;">
            <span class="provider-badge" style="background:{c['badge']};">{m['provider'].upper()}</span>
            <span class="model-name">{m['model']}</span>
          </div>
          <div class="card-body">{body}</div>
          {footer}
        </div>"""

    insight_vals = [
        ("💰", "Most Cost-Effective", ins["cheapest"]),
        ("⚡", "Fastest Response",    ins["fastest"]),
        ("📝", "Most Detailed",       ins["most_detail"]),
        ("🚀", "Best Throughput",     ins["best_tps"]),
    ]
    insights_html = "".join(
        f'<div class="insight-item"><span class="insight-icon">{icon}</span>'
        f'<div><div class="insight-label">{label}</div>'
        f'<div class="insight-model">{model}</div></div></div>'
        for icon, label, model in insight_vals
    )

    table_rows = ""
    for m in models:
        if m["error"]:
            table_rows += f"""
            <tr class="error-row">
              <td>{m['model']}</td><td>—</td><td>—</td><td>—</td>
              <td>—</td><td>—</td><td>—</td>
            </tr>"""
        else:
            table_rows += f"""
            <tr>
              <td><strong>{m['model']}</strong></td>
              <td class="num">{m['input']:,}</td>
              <td class="num">{m['output']:,}</td>
              <td class="num num-bold">{m['total']:,}</td>
              <td class="num cost">${m['cost']:.6f}</td>
              <td class="num">{m['time']:.2f}s</td>
              <td class="num">{m['tps']:.1f}</td>
            </tr>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Token Analysis Report</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
  :root {{
    --bg: #0f172a; --surface: #1e293b; --surface2: #263244;
    --border: #334155; --text: #e2e8f0; --muted: #94a3b8;
    --accent: #38bdf8; --green: #4ade80; --yellow: #fbbf24;
    --red: #f87171; --orange: #fb923c; --indigo: #818cf8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ background: var(--bg); color: var(--text); font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; }}

  /* ── Layout ── */
  .container {{ max-width: 1400px; margin: 0 auto; padding: 24px 20px; }}
  h1, h2, h3 {{ font-weight: 600; }}
  .section {{ margin-bottom: 40px; }}
  .section-title {{ font-size: 1.1rem; font-weight: 600; color: var(--accent); text-transform: uppercase;
                    letter-spacing: .06em; border-left: 3px solid var(--accent); padding-left: 10px;
                    margin-bottom: 20px; }}

  /* ── Header ── */
  .page-header {{ background: linear-gradient(135deg, #0f2035 0%, #1a1040 100%);
                  border: 1px solid var(--border); border-radius: 12px;
                  padding: 28px 32px; margin-bottom: 32px; }}
  .page-header h1 {{ font-size: 1.6rem; background: linear-gradient(90deg, #38bdf8, #818cf8);
                     -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
  .page-header .meta {{ color: var(--muted); font-size: .85rem; margin-top: 6px; }}
  .prompt-box {{ background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
                 padding: 14px 18px; margin-top: 16px; font-size: 1.05rem; color: var(--text); }}
  .prompt-label {{ font-size: .75rem; color: var(--accent); text-transform: uppercase;
                   letter-spacing: .08em; margin-bottom: 4px; }}

  /* ── Insights ── */
  .insights-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; }}
  .insight-item {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px;
                   padding: 16px 18px; display: flex; align-items: center; gap: 14px; }}
  .insight-icon {{ font-size: 1.8rem; }}
  .insight-label {{ font-size: .78rem; color: var(--muted); text-transform: uppercase; letter-spacing: .06em; }}
  .insight-model {{ font-weight: 600; color: var(--text); font-size: .95rem; margin-top: 2px; }}

  /* ── Charts ── */
  .charts-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(480px, 1fr)); gap: 20px; }}
  .chart-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 20px; }}
  .chart-card h3 {{ font-size: .9rem; color: var(--muted); margin-bottom: 14px; text-transform: uppercase; letter-spacing: .05em; }}
  .chart-wrap {{ position: relative; height: 260px; }}

  /* ── Token bar mini-chart per model ── */
  .token-bars {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 20px; }}
  .token-bar-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 10px; padding: 18px 20px; }}
  .token-bar-card .model-label {{ font-weight: 600; margin-bottom: 12px; font-size: .9rem; }}
  .bar-row {{ display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: .82rem; }}
  .bar-row .bar-label {{ width: 56px; color: var(--muted); flex-shrink: 0; }}
  .bar-track {{ flex: 1; background: #ffffff0f; border-radius: 4px; height: 10px; overflow: hidden; }}
  .bar-fill {{ height: 100%; border-radius: 4px; transition: width .6s ease; }}
  .bar-value {{ width: 60px; text-align: right; color: var(--text); flex-shrink: 0; }}

  /* ── Response cards ── */
  .responses-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }}
  .response-card {{ border: 1px solid; border-radius: 10px; overflow: hidden; display: flex; flex-direction: column; }}
  .card-header {{ padding: 12px 16px; display: flex; align-items: center; gap: 10px; }}
  .provider-badge {{ font-size: .7rem; font-weight: 700; letter-spacing: .08em; padding: 2px 8px; border-radius: 999px; color: #fff; }}
  .model-name {{ font-weight: 600; font-size: .95rem; color: #e2e8f0; }}
  .card-body {{ padding: 16px; flex: 1; }}
  .response-text {{ white-space: pre-wrap; word-break: break-word; font-family: inherit; font-size: .88rem; color: #cbd5e1; line-height: 1.7; }}
  .error-msg {{ color: #f87171; font-size: .9rem; }}
  .card-footer {{ padding: 10px 16px; display: flex; flex-wrap: wrap; gap: 6px; border-top: 1px solid #ffffff10; }}
  .badge {{ font-size: .72rem; padding: 3px 8px; border-radius: 999px; font-weight: 600; }}
  .badge-in    {{ background: #1e3a5f; color: #60a5fa; }}
  .badge-out   {{ background: #14402a; color: #4ade80; }}
  .badge-total {{ background: #3d2e06; color: #fbbf24; }}
  .badge-cost  {{ background: #3d0f0f; color: #f87171; }}
  .badge-time  {{ background: #1e1b4b; color: #818cf8; }}
  .badge-tps   {{ background: #3d1f00; color: #fb923c; }}

  /* ── Summary table ── */
  .table-wrap {{ overflow-x: auto; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .9rem; }}
  thead tr {{ background: var(--surface2); }}
  th {{ padding: 11px 14px; text-align: left; color: var(--muted); font-weight: 600;
        font-size: .78rem; text-transform: uppercase; letter-spacing: .05em; border-bottom: 1px solid var(--border); }}
  td {{ padding: 11px 14px; border-bottom: 1px solid var(--border); vertical-align: middle; }}
  tr:hover td {{ background: var(--surface2); }}
  .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
  .num-bold {{ font-weight: 700; color: var(--yellow); }}
  .cost {{ color: var(--red); }}
  .error-row td {{ color: var(--muted); }}

  /* ── Footer ── */
  .page-footer {{ text-align: center; color: var(--muted); font-size: .8rem; padding: 20px 0; margin-top: 8px; border-top: 1px solid var(--border); }}
</style>
</head>
<body>
<div class="container">

  <!-- Header -->
  <div class="page-header">
    <h1>Token Analysis Report</h1>
    <div class="meta">Generated on {p['timestamp']}</div>
    <div class="prompt-label" style="margin-top:14px;">Prompt</div>
    <div class="prompt-box">{p['prompt']}</div>
  </div>

  <!-- Insights -->
  <div class="section">
    <div class="section-title">Key Insights</div>
    <div class="insights-grid">
      {insights_html}
    </div>
  </div>

  <!-- Per-model token bars -->
  <div class="section">
    <div class="section-title">Token Breakdown per Model</div>
    <div class="token-bars" id="tokenBars"></div>
  </div>

  <!-- Charts 2x2 -->
  <div class="section">
    <div class="section-title">Comparative Charts</div>
    <div class="charts-grid">
      <div class="chart-card">
        <h3>Input vs Output Tokens</h3>
        <div class="chart-wrap"><canvas id="chartTokens"></canvas></div>
      </div>
      <div class="chart-card">
        <h3>Estimated Cost (USD)</h3>
        <div class="chart-wrap"><canvas id="chartCost"></canvas></div>
      </div>
      <div class="chart-card">
        <h3>Response Time (seconds)</h3>
        <div class="chart-wrap"><canvas id="chartTime"></canvas></div>
      </div>
      <div class="chart-card">
        <h3>Throughput (tokens / second)</h3>
        <div class="chart-wrap"><canvas id="chartTps"></canvas></div>
      </div>
    </div>
  </div>

  <!-- Responses -->
  <div class="section">
    <div class="section-title">Model Responses</div>
    <div class="responses-grid">
      {cards_html}
    </div>
  </div>

  <!-- Summary table -->
  <div class="section">
    <div class="section-title">Summary Table</div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Model</th><th>Input Tokens</th><th>Output Tokens</th>
            <th>Total Tokens</th><th>Est. Cost</th><th>Time (s)</th><th>Tok/s</th>
          </tr>
        </thead>
        <tbody>{table_rows}</tbody>
      </table>
    </div>
  </div>

  <div class="page-footer">token-analysis v1.0.0 &nbsp;·&nbsp; {p['timestamp']}</div>
</div>

<script>
const DATA = {data_json};
const MODELS  = {model_labels};
const BORDERS = {border_colors};
const INPUT   = {input_data};
const OUTPUT  = {output_data};
const TOTAL   = {total_data};
const COST    = {cost_data};
const TIME    = {time_data};
const TPS     = {tps_data};

const chartDefaults = {{
  responsive: true,
  maintainAspectRatio: false,
  plugins: {{
    legend: {{ labels: {{ color: '#94a3b8', font: {{ size: 12 }} }} }},
    tooltip: {{ backgroundColor: '#1e293b', titleColor: '#e2e8f0', bodyColor: '#94a3b8',
                borderColor: '#334155', borderWidth: 1 }},
  }},
  scales: {{
    x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#ffffff0d' }} }},
    y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: '#ffffff0d' }} }},
  }},
}};

// Chart 1 — grouped bar: input vs output
new Chart(document.getElementById('chartTokens'), {{
  type: 'bar',
  data: {{
    labels: MODELS,
    datasets: [
      {{ label: 'Input Tokens',  data: INPUT,  backgroundColor: 'rgba(96,165,250,0.8)',  borderRadius: 4 }},
      {{ label: 'Output Tokens', data: OUTPUT, backgroundColor: 'rgba(74,222,128,0.8)',  borderRadius: 4 }},
    ],
  }},
  options: {{ ...chartDefaults }},
}});

// Chart 2 — cost
new Chart(document.getElementById('chartCost'), {{
  type: 'bar',
  data: {{
    labels: MODELS,
    datasets: [{{ label: 'Cost (USD)', data: COST,
      backgroundColor: BORDERS.map(c => c + '99'), borderColor: BORDERS,
      borderWidth: 2, borderRadius: 4 }}],
  }},
  options: {{ ...chartDefaults,
    plugins: {{ ...chartDefaults.plugins,
      tooltip: {{ ...chartDefaults.plugins.tooltip,
        callbacks: {{ label: ctx => ' $' + ctx.raw.toFixed(6) }} }},
    }},
  }},
}});

// Chart 3 — response time
new Chart(document.getElementById('chartTime'), {{
  type: 'bar',
  data: {{
    labels: MODELS,
    datasets: [{{ label: 'Response Time (s)', data: TIME,
      backgroundColor: 'rgba(129,140,248,0.8)', borderRadius: 4 }}],
  }},
  options: {{ ...chartDefaults,
    plugins: {{ ...chartDefaults.plugins,
      tooltip: {{ ...chartDefaults.plugins.tooltip,
        callbacks: {{ label: ctx => ' ' + ctx.raw.toFixed(3) + 's' }} }},
    }},
  }},
}});

// Chart 4 — throughput
new Chart(document.getElementById('chartTps'), {{
  type: 'bar',
  data: {{
    labels: MODELS,
    datasets: [{{ label: 'Tokens / Second', data: TPS,
      backgroundColor: 'rgba(251,146,60,0.8)', borderRadius: 4 }}],
  }},
  options: {{ ...chartDefaults }},
}});

// Per-model horizontal token bar cards
const barsContainer = document.getElementById('tokenBars');
DATA.models.forEach(m => {{
  if (m.error) return;
  const max = m.total;
  const pct = v => max > 0 ? (v / max * 100).toFixed(1) : 0;
  barsContainer.innerHTML += `
    <div class="token-bar-card" style="border:1px solid ${{m.colors.border}}40">
      <div class="model-label" style="color:${{m.colors.border}}">${{m.model}}</div>
      <div class="bar-row">
        <span class="bar-label">Input</span>
        <div class="bar-track"><div class="bar-fill" style="width:${{pct(m.input)}}%;background:#60a5fa"></div></div>
        <span class="bar-value">${{m.input.toLocaleString()}}</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Output</span>
        <div class="bar-track"><div class="bar-fill" style="width:${{pct(m.output)}}%;background:#4ade80"></div></div>
        <span class="bar-value">${{m.output.toLocaleString()}}</span>
      </div>
      <div class="bar-row">
        <span class="bar-label">Total</span>
        <div class="bar-track"><div class="bar-fill" style="width:100%;background:#fbbf24"></div></div>
        <span class="bar-value">${{m.total.toLocaleString()}}</span>
      </div>
    </div>`;
}});
</script>
</body>
</html>"""
