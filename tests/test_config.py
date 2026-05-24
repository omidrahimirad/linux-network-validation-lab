from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from netlab_validator.config import ScenarioConfig, load_scenario


def test_load_baseline_config() -> None:
    scenario = load_scenario(Path("configs/baseline.yaml"))

    assert scenario.name == "baseline"
    assert scenario.target.host == "172.31.0.10"
    assert scenario.fault.enabled is False
    assert scenario.thresholds.require_expected_hops is True


def test_enabled_fault_requires_impairment() -> None:
    with pytest.raises(ValidationError):
        ScenarioConfig.model_validate(
            {
                "name": "bad",
                "description": "invalid",
                "target": {"host": "172.31.0.10"},
                "fault": {"enabled": True, "interface": "eth1"},
                "thresholds": {
                    "max_avg_latency_ms": 1,
                    "max_packet_loss_percent": 0,
                    "min_throughput_mbps": 1,
                },
            }
        )
