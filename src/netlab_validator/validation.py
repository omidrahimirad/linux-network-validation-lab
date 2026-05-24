from __future__ import annotations

from dataclasses import dataclass

from netlab_validator.config import ScenarioConfig
from netlab_validator.metrics import IperfMetrics, PingMetrics, TracerouteMetrics


@dataclass(frozen=True)
class ValidationCheck:
    name: str
    passed: bool
    observed: float | str | list[str] | None
    threshold: float | str | list[str] | None
    detail: str


def expected_hops_present(observed: list[str], expected: list[str]) -> bool:
    if not expected:
        return True
    position = 0
    for hop in observed:
        if hop == expected[position]:
            position += 1
            if position == len(expected):
                return True
    return False


def validate_results(
    scenario: ScenarioConfig,
    ping: PingMetrics,
    iperf: IperfMetrics,
    traceroute: TracerouteMetrics,
) -> list[ValidationCheck]:
    thresholds = scenario.thresholds
    checks = [
        ValidationCheck(
            name="packet_loss",
            passed=ping.packet_loss_percent <= thresholds.max_packet_loss_percent,
            observed=ping.packet_loss_percent,
            threshold=thresholds.max_packet_loss_percent,
            detail="Ping packet loss must remain within the scenario threshold.",
        ),
        ValidationCheck(
            name="avg_latency",
            passed=ping.avg_latency_ms is not None
            and ping.avg_latency_ms <= thresholds.max_avg_latency_ms,
            observed=ping.avg_latency_ms,
            threshold=thresholds.max_avg_latency_ms,
            detail="Average ICMP round-trip latency must remain within threshold.",
        ),
        ValidationCheck(
            name="min_throughput",
            passed=iperf.throughput_mbps >= thresholds.min_throughput_mbps,
            observed=round(iperf.throughput_mbps, 3),
            threshold=thresholds.min_throughput_mbps,
            detail="iperf3 measured throughput must meet the minimum target.",
        ),
    ]
    if thresholds.max_throughput_mbps is not None:
        checks.append(
            ValidationCheck(
                name="max_throughput",
                passed=iperf.throughput_mbps <= thresholds.max_throughput_mbps,
                observed=round(iperf.throughput_mbps, 3),
                threshold=thresholds.max_throughput_mbps,
                detail="Measured throughput should remain near the configured rate limit.",
            )
        )
    if thresholds.require_expected_hops:
        checks.append(
            ValidationCheck(
                name="expected_hops",
                passed=expected_hops_present(traceroute.hops, scenario.target.expected_hops),
                observed=traceroute.hops,
                threshold=scenario.target.expected_hops,
                detail="Traceroute must include the expected routed path in order.",
            )
        )
    return checks


def overall_status(checks: list[ValidationCheck]) -> str:
    return "pass" if all(check.passed for check in checks) else "fail"
