from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, cast

from jinja2 import Template


def write_results_json(results: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2, sort_keys=True), encoding="utf-8")


def write_results_csv(results: dict[str, object], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    test_results = _as_mapping(results["test_results"])
    validations = [_as_mapping(item) for item in _as_list(results["validations"])]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["section", "metric", "value"])
        writer.writeheader()
        for section, values in test_results.items():
            for metric, value in _as_mapping(values).items():
                writer.writerow({"section": section, "metric": metric, "value": value})
        for check in validations:
            writer.writerow(
                {
                    "section": "validation",
                    "metric": str(check["name"]),
                    "value": f"{check['passed']} observed={check['observed']}",
                }
            )


def load_results(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def generate_html_report(results: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(_template().render(results=results), encoding="utf-8")


def _as_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("expected mapping")
    return value


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise TypeError("expected list")
    return value


def _template() -> Template:
    return Template(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Network Validation Report - {{ results.scenario.name }}</title>
  <style>
    :root {
      color-scheme: light;
      --ink: #17202a;
      --muted: #566573;
      --line: #d5d8dc;
      --ok: #176f43;
      --bad: #9a3412;
    }
    body {
      margin: 0;
      font-family: Arial, Helvetica, sans-serif;
      color: var(--ink);
      background: #f7f9fa;
    }
    main { max-width: 1120px; margin: 0 auto; padding: 32px 24px 48px; }
    h1, h2 { margin: 0 0 12px; }
    h1 { font-size: 28px; }
    h2 {
      font-size: 18px;
      margin-top: 28px;
      border-bottom: 1px solid var(--line);
      padding-bottom: 8px;
    }
    p { line-height: 1.5; }
    .summary {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin: 20px 0;
    }
    .tile {
      background: white;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 14px;
    }
    .label {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: .04em;
    }
    .value { font-size: 20px; font-weight: 700; margin-top: 6px; }
    .pass { color: var(--ok); }
    .fail { color: var(--bad); }
    table {
      width: 100%;
      border-collapse: collapse;
      background: white;
      border: 1px solid var(--line);
    }
    th, td {
      text-align: left;
      border-bottom: 1px solid var(--line);
      padding: 9px 10px;
      vertical-align: top;
      font-size: 14px;
    }
    th { background: #edf1f2; }
    pre {
      white-space: pre-wrap;
      background: #111827;
      color: #e5e7eb;
      padding: 12px;
      border-radius: 6px;
      overflow-x: auto;
    }
    code { font-family: Menlo, Consolas, monospace; font-size: 12px; }
    .topology {
      font-family: Menlo, Consolas, monospace;
      background: white;
      border: 1px solid var(--line);
      border-radius: 6px;
      padding: 16px;
    }
    @media (max-width: 760px) {
      .summary { grid-template-columns: 1fr; }
      main { padding: 20px 14px; }
    }
  </style>
</head>
<body>
<main>
  <h1>Network Validation Report</h1>
  <p>{{ results.scenario.description }}</p>

  <section class="summary">
    <div class="tile">
      <div class="label">Scenario</div>
      <div class="value">{{ results.scenario.name }}</div>
    </div>
    <div class="tile">
      <div class="label">Status</div>
      <div class="value {{ results.status }}">{{ results.status|upper }}</div>
    </div>
    <div class="tile">
      <div class="label">Avg Latency</div>
      <div class="value">{{ results.test_results.ping.avg_latency_ms }} ms</div>
    </div>
    <div class="tile">
      <div class="label">Throughput</div>
      <div class="value">
        {{ "%.2f"|format(results.test_results.iperf3.throughput_mbps) }} Mbps
      </div>
    </div>
  </section>

  <h2>Executive Summary</h2>
  <p>
    The lab executed a controlled validation run for <strong>{{ results.scenario.name }}</strong>.
    Overall status is <strong class="{{ results.status }}">{{ results.status|upper }}</strong>.
    The result reflects this Docker-based topology and the thresholds declared in the scenario file.
  </p>

  <h2>Scenario Configuration</h2>
  <pre><code>{{ results.scenario | tojson(indent=2) }}</code></pre>

  <h2>Topology</h2>
  <div class="topology">
linux-client (172.30.0.10)
  -> linux-router (172.30.0.254 / 172.31.0.254)
  -> linux-server (172.31.0.10)
  </div>

  <h2>Fault Injection Parameters</h2>
  <table>
    <tr><th>Parameter</th><th>Value</th></tr>
    {% for key, value in results.fault_injection.items() %}
    <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
    {% endfor %}
  </table>

  <h2>Test Results</h2>
  <table>
    <tr><th>Test</th><th>Metric</th><th>Value</th></tr>
    {% for test_name, metrics in results.test_results.items() %}
      {% for metric, value in metrics.items() %}
      <tr><td>{{ test_name }}</td><td>{{ metric }}</td><td>{{ value }}</td></tr>
      {% endfor %}
    {% endfor %}
  </table>

  <h2>Threshold Validation</h2>
  <table>
    <tr><th>Check</th><th>Status</th><th>Observed</th><th>Threshold</th><th>Detail</th></tr>
    {% for check in results.validations %}
    <tr>
      <td>{{ check.name }}</td>
      <td class="{{ 'pass' if check.passed else 'fail' }}">
        {{ 'PASS' if check.passed else 'FAIL' }}
      </td>
      <td>{{ check.observed }}</td>
      <td>{{ check.threshold }}</td>
      <td>{{ check.detail }}</td>
    </tr>
    {% endfor %}
  </table>

  <h2>Engineering Interpretation</h2>
  <p>{{ results.engineering_interpretation }}</p>

  <h2>Troubleshooting Recommendations</h2>
  <ul>
    {% for item in results.troubleshooting_recommendations %}
    <li>{{ item }}</li>
    {% endfor %}
  </ul>

  <h2>Raw Command Summary</h2>
  <table>
    <tr><th>Command</th><th>Exit</th><th>Elapsed</th></tr>
    {% for command in results.raw_commands %}
    <tr>
      <td><code>{{ command.command }}</code></td>
      <td>{{ command.returncode }}</td>
      <td>{{ command.elapsed_seconds }} s</td>
    </tr>
    {% endfor %}
  </table>
</main>
</body>
</html>
"""
    )
