from __future__ import annotations

import json
from pathlib import Path

from netlab_validator.reporting import (
    generate_html_report,
    merge_result_archive,
    write_results_csv,
    write_results_json,
)


def sample_results() -> dict[str, object]:
    return {
        "generated_at": "2026-05-24T00:00:00+00:00",
        "scenario": {"name": "baseline", "description": "Nominal", "thresholds": {}},
        "topology": {"client": "linux-client"},
        "fault_injection": {"enabled": False, "interface": "eth1"},
        "fault_commands": [],
        "test_results": {
            "ping": {"avg_latency_ms": 0.1, "packet_loss_percent": 0},
            "iperf3": {"throughput_mbps": 500.0},
            "traceroute": {"hops": ["172.30.0.254", "172.31.0.10"]},
        },
        "validations": [
            {
                "name": "packet_loss",
                "passed": True,
                "observed": 0,
                "threshold": 0,
                "detail": "ok",
            }
        ],
        "status": "pass",
        "engineering_interpretation": "Lab result is acceptable.",
        "troubleshooting_recommendations": ["Keep scenario files with the run."],
        "raw_commands": [
            {
                "command": "docker exec linux-client ping",
                "returncode": 0,
                "elapsed_seconds": 1,
            }
        ],
    }


def test_write_results_json_and_csv(tmp_path: Path) -> None:
    results = sample_results()
    json_path = tmp_path / "results.json"
    csv_path = tmp_path / "results.csv"

    write_results_json(results, json_path)
    write_results_csv(results, csv_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == "pass"
    assert "baseline,validation,packet_loss" in csv_path.read_text(encoding="utf-8")


def test_generate_html_report(tmp_path: Path) -> None:
    output = tmp_path / "report.html"

    generate_html_report(sample_results(), output)

    html = output.read_text(encoding="utf-8")
    assert "Executive Summary" in html
    assert "Network Validation Report" in html
    assert "Threshold Validation" in html


def test_merge_result_archive_replaces_existing_scenario() -> None:
    first = sample_results()
    replacement = sample_results()
    replacement["test_results"] = {
        "ping": {"avg_latency_ms": 0.2, "packet_loss_percent": 0},
        "iperf3": {"throughput_mbps": 600.0},
        "traceroute": {"hops": ["172.30.0.254", "172.31.0.10"]},
    }

    archive = merge_result_archive(None, first)
    archive = merge_result_archive(archive, replacement)

    assert archive["status"] == "pass"
    assert len(archive["runs"]) == 1
    assert archive["runs"][0]["test_results"]["iperf3"]["throughput_mbps"] == 600.0
