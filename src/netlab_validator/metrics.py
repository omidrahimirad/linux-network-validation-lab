from __future__ import annotations

import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PingMetrics:
    transmitted: int
    received: int
    packet_loss_percent: float
    min_latency_ms: float | None
    avg_latency_ms: float | None
    max_latency_ms: float | None
    mdev_latency_ms: float | None


@dataclass(frozen=True)
class IperfMetrics:
    throughput_mbps: float
    retransmits: int | None
    seconds: float


@dataclass(frozen=True)
class TracerouteMetrics:
    hops: list[str]


def parse_ping(output: str) -> PingMetrics:
    packet_match = re.search(
        r"(?P<tx>\d+) packets transmitted, (?P<rx>\d+) (?:packets )?received, "
        r"(?P<loss>[\d.]+)% packet loss",
        output,
    )
    if packet_match is None:
        raise ValueError("unable to parse ping packet summary")

    rtt_match = re.search(
        r"(?:rtt|round-trip) min/avg/max/(?:mdev|stddev) = "
        r"(?P<min>[\d.]+)/(?P<avg>[\d.]+)/(?P<max>[\d.]+)/(?P<mdev>[\d.]+) ms",
        output,
    )
    return PingMetrics(
        transmitted=int(packet_match.group("tx")),
        received=int(packet_match.group("rx")),
        packet_loss_percent=float(packet_match.group("loss")),
        min_latency_ms=float(rtt_match.group("min")) if rtt_match else None,
        avg_latency_ms=float(rtt_match.group("avg")) if rtt_match else None,
        max_latency_ms=float(rtt_match.group("max")) if rtt_match else None,
        mdev_latency_ms=float(rtt_match.group("mdev")) if rtt_match else None,
    )


def parse_iperf3_json(output: str) -> IperfMetrics:
    payload = json.loads(output)
    end = payload["end"]
    summary = end.get("sum_received") or end["sum_sent"]
    bits_per_second = float(summary["bits_per_second"])
    retransmits = summary.get("retransmits")
    return IperfMetrics(
        throughput_mbps=bits_per_second / 1_000_000,
        retransmits=int(retransmits) if retransmits is not None else None,
        seconds=float(summary["seconds"]),
    )


def parse_traceroute(output: str) -> TracerouteMetrics:
    hops: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("traceroute"):
            continue
        match = re.search(r"(?:^|\s)(\d{1,3}(?:\.\d{1,3}){3})(?:\s|$)", stripped)
        if match:
            hops.append(match.group(1))
    if not hops:
        raise ValueError("unable to parse traceroute hops")
    return TracerouteMetrics(hops=hops)
