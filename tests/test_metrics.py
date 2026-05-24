from __future__ import annotations

from netlab_validator.metrics import parse_iperf3_json, parse_ping, parse_traceroute


def test_parse_ping_linux_output() -> None:
    output = """
5 packets transmitted, 5 received, 0% packet loss, time 4095ms
rtt min/avg/max/mdev = 0.052/0.078/0.118/0.023 ms
"""
    metrics = parse_ping(output)

    assert metrics.transmitted == 5
    assert metrics.received == 5
    assert metrics.packet_loss_percent == 0
    assert metrics.avg_latency_ms == 0.078


def test_parse_iperf3_json() -> None:
    output = """
{
  "end": {
    "sum_received": {
      "seconds": 3.0001,
      "bits_per_second": 942000000.0
    }
  }
}
"""
    metrics = parse_iperf3_json(output)

    assert metrics.throughput_mbps == 942
    assert metrics.seconds == 3.0001


def test_parse_traceroute_output() -> None:
    output = """
traceroute to 172.31.0.10 (172.31.0.10), 5 hops max
 1  172.30.0.254  0.123 ms
 2  172.31.0.10  0.211 ms
"""
    metrics = parse_traceroute(output)

    assert metrics.hops == ["172.30.0.254", "172.31.0.10"]
