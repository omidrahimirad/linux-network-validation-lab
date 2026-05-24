# Engineering Assumptions

- The host has Docker and Docker Compose available.
- The lab is run on a Linux-compatible Docker environment.
- Docker can assign the configured static subnets without conflicting with existing local networks.
- The router interface names are pinned by Compose as `eth0` for the client network and `eth1` for
  the server network.
- The server endpoint is `172.31.0.10` and runs `iperf3 --server`.
- Thresholds are scenario-specific and should be reviewed before using a result as evidence.
- Results are intended for local validation and regression comparison, not production service-level
  monitoring.

## Reproducibility Notes

The lab clears existing qdisc state before applying scenario faults. This improves repeatability, but
measurements can still vary with host CPU load, Docker networking implementation, and concurrent
traffic on the machine.
