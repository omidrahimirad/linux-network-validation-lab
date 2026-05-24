from __future__ import annotations

from netlab_validator.config import load_scenario
from netlab_validator.metrics import IperfMetrics, PingMetrics, TracerouteMetrics
from netlab_validator.validation import expected_hops_present, overall_status, validate_results


def test_expected_hops_present_in_order() -> None:
    assert expected_hops_present(["172.30.0.254", "172.31.0.10"], ["172.31.0.10"])
    assert not expected_hops_present(["172.31.0.10"], ["172.30.0.254", "172.31.0.10"])


def test_threshold_validation_passes_baseline() -> None:
    scenario = load_scenario("configs/baseline.yaml")
    checks = validate_results(
        scenario,
        PingMetrics(
            transmitted=5,
            received=5,
            packet_loss_percent=0,
            min_latency_ms=0.05,
            avg_latency_ms=0.08,
            max_latency_ms=0.12,
            mdev_latency_ms=0.02,
        ),
        IperfMetrics(throughput_mbps=500, retransmits=0, seconds=3),
        TracerouteMetrics(hops=["172.30.0.254", "172.31.0.10"]),
    )

    assert overall_status(checks) == "pass"


def test_threshold_validation_fails_packet_loss() -> None:
    scenario = load_scenario("configs/baseline.yaml")
    checks = validate_results(
        scenario,
        PingMetrics(
            transmitted=5,
            received=4,
            packet_loss_percent=20,
            min_latency_ms=0.05,
            avg_latency_ms=0.08,
            max_latency_ms=0.12,
            mdev_latency_ms=0.02,
        ),
        IperfMetrics(throughput_mbps=500, retransmits=0, seconds=3),
        TracerouteMetrics(hops=["172.30.0.254", "172.31.0.10"]),
    )

    assert overall_status(checks) == "fail"
