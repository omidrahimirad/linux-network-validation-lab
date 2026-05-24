# Test Scenarios

Scenario files are intentionally plain YAML so test parameters and acceptance thresholds are
reviewable in code review.

## Baseline

`configs/baseline.yaml` validates the nominal routed path without impairment. It is useful as a
sanity check before running degraded scenarios.

## Latency Degradation

`configs/latency_degradation.yaml` injects delay on the router egress interface toward the server.
The threshold allows higher average round-trip time while still requiring successful forwarding and
minimum throughput.

## Packet Loss

`configs/packet_loss.yaml` injects packet loss and uses a larger ping sample count so the measured
loss percentage has enough observations to be meaningful in a small lab.

## Bandwidth Limit

`configs/bandwidth_limit.yaml` applies a `netem rate` limit. The scenario validates both a minimum
throughput and an upper bound so the report can show whether the rate limit materially affected the
flow.

## Optional Packet Capture

Each scenario can enable capture:

```yaml
capture:
  enabled: true
  interface: eth0
  duration_seconds: 10
```

Captures are written under `reports/captures/` from the client container volume mount.
