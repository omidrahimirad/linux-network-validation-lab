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
    runs = _result_runs(results)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["scenario", "section", "metric", "value"],
            lineterminator="\n",
        )
        writer.writeheader()
        for run in runs:
            scenario_name = _scenario_name(run)
            test_results = _as_mapping(run["test_results"])
            validations = [_as_mapping(item) for item in _as_list(run["validations"])]
            for section, values in test_results.items():
                for metric, value in _as_mapping(values).items():
                    writer.writerow(
                        {
                            "scenario": scenario_name,
                            "section": section,
                            "metric": metric,
                            "value": value,
                        }
                    )
            for check in validations:
                writer.writerow(
                    {
                        "scenario": scenario_name,
                        "section": "validation",
                        "metric": str(check["name"]),
                        "value": f"{check['passed']} observed={check['observed']}",
                    }
                )


def load_results(path: Path) -> dict[str, object]:
    return cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))


def generate_html_report(results: dict[str, object], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    rendered = _template().render(report=_report_view(results))
    clean_html = "\n".join(line.rstrip() for line in rendered.splitlines()) + "\n"
    output.write_text(clean_html, encoding="utf-8")


def merge_result_archive(
    existing: dict[str, object] | None,
    new_result: dict[str, object],
) -> dict[str, object]:
    runs: list[dict[str, object]] = []
    if existing is not None:
        runs.extend(_result_runs(existing))

    new_name = _scenario_name(new_result)
    runs = [run for run in runs if _scenario_name(run) != new_name]
    runs.append(new_result)

    return {
        "generated_at": new_result["generated_at"],
        "status": "pass" if all(run.get("status") == "pass" for run in runs) else "fail",
        "topology": new_result["topology"],
        "runs": runs,
    }


def _as_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("expected mapping")
    return value


def _as_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise TypeError("expected list")
    return value


def _result_runs(results: dict[str, object]) -> list[dict[str, object]]:
    if "runs" in results:
        return [_as_object_mapping(item) for item in _as_list(results["runs"])]
    return [results]


def _as_object_mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError("expected mapping")
    return cast(dict[str, object], value)


def _scenario_name(result: dict[str, object]) -> str:
    scenario = _as_mapping(result["scenario"])
    return str(scenario["name"])


def _test_metric(result: dict[str, object], test: str, metric: str) -> object:
    test_results = _as_mapping(result["test_results"])
    return _as_mapping(test_results[test])[metric]


def _report_view(results: dict[str, object]) -> dict[str, object]:
    runs = _result_runs(results)
    return {
        "generated_at": results.get("generated_at"),
        "status": "pass" if all(run.get("status") == "pass" for run in runs) else "fail",
        "topology": results.get("topology", runs[-1].get("topology")),
        "runs": runs,
        "summary": [
            {
                "scenario": _scenario_name(run),
                "status": run["status"],
                "avg_latency_ms": _test_metric(run, "ping", "avg_latency_ms"),
                "packet_loss_percent": _test_metric(run, "ping", "packet_loss_percent"),
                "throughput_mbps": _test_metric(run, "iperf3", "throughput_mbps"),
            }
            for run in runs
        ],
    }


def _template() -> Template:
    return Template(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Network Validation Report</title>
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
  <p>
    Docker-based Linux network validation evidence for connectivity, latency,
    packet-loss, throughput, and tc/netem fault injection.
  </p>

  <section class="summary">
    <div class="tile">
      <div class="label">Scenarios</div>
      <div class="value">{{ report.runs | length }}</div>
    </div>
    <div class="tile">
      <div class="label">Status</div>
      <div class="value {{ report.status }}">{{ report.status|upper }}</div>
    </div>
    <div class="tile">
      <div class="label">Topology</div>
      <div class="value">3 nodes</div>
    </div>
    <div class="tile">
      <div class="label">Output</div>
      <div class="value">JSON / CSV / HTML</div>
    </div>
  </section>

  <h2>Executive Summary</h2>
  <p>
    The lab executed <strong>{{ report.runs | length }}</strong> controlled validation scenario(s).
    Overall status is <strong class="{{ report.status }}">{{ report.status|upper }}</strong>.
    Results are container-lab measurements and should not be treated as physical-network accuracy.
  </p>

  <h2>Topology</h2>
  <div class="topology">
linux-client (172.30.0.10)
  -> linux-router (172.30.0.254 / 172.31.0.254)
  -> linux-server (172.31.0.10)
  </div>

  <h2>Scenario Results</h2>
  <table>
    <tr>
      <th>Scenario</th>
      <th>Status</th>
      <th>Avg Latency</th>
      <th>Packet Loss</th>
      <th>Throughput</th>
    </tr>
    {% for item in report.summary %}
    <tr>
      <td>{{ item.scenario }}</td>
      <td class="{{ item.status }}">{{ item.status|upper }}</td>
      <td>{{ item.avg_latency_ms }} ms</td>
      <td>{{ item.packet_loss_percent }}%</td>
      <td>{{ "%.3f"|format(item.throughput_mbps) }} Mbps</td>
    </tr>
    {% endfor %}
  </table>

  {% for run in report.runs %}
  <h2>{{ run.scenario.name }} Details</h2>
  <p>{{ run.scenario.description }}</p>

  <h2>Fault Injection Parameters</h2>
  <table>
    <tr><th>Parameter</th><th>Value</th></tr>
    {% for key, value in run.fault_injection.items() %}
    <tr><td>{{ key }}</td><td>{{ value }}</td></tr>
    {% endfor %}
  </table>

  <h2>Threshold Validation</h2>
  <table>
    <tr><th>Check</th><th>Status</th><th>Observed</th><th>Threshold</th><th>Detail</th></tr>
    {% for check in run.validations %}
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
  <p>{{ run.engineering_interpretation }}</p>

  <h2>Troubleshooting Recommendations</h2>
  <ul>
    {% for item in run.troubleshooting_recommendations %}
    <li>{{ item }}</li>
    {% endfor %}
  </ul>

  <h2>Raw Command Summary</h2>
  <table>
    <tr><th>Command</th><th>Exit</th><th>Elapsed</th></tr>
    {% for command in run.raw_commands %}
    <tr>
      <td><code>{{ command.command }}</code></td>
      <td>{{ command.returncode }}</td>
      <td>{{ command.elapsed_seconds }} s</td>
    </tr>
    {% endfor %}
  </table>
  {% endfor %}
</main>
</body>
</html>
"""
    )
