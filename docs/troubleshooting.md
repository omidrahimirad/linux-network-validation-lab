# Troubleshooting

## Containers Are Not Running

```bash
docker compose ps
docker compose up -d --build
```

If image builds fail, confirm Docker is running and the host can pull Debian package indexes.

## macOS And Docker Desktop

Fault injection is executed inside Linux containers using `tc/netem`. The project can be launched
from macOS using Docker Desktop, but the network behavior is validated inside Linux containers.
Docker daemon availability, Docker Desktop resource limits, and container networking permissions can
affect integration tests.

Notes:

- `NET_ADMIN` capability is required for traffic-control operations.
- Docker Desktop must be running before integration tests.
- Docker daemon problems are environment issues, not necessarily project failures.
- Linux-native execution may be more predictable for `tc/netem` validation.
- macOS itself does not run `tc/netem` directly in this project.

## Client Cannot Reach Server

Inspect routes:

```bash
docker exec linux-client ip route
docker exec linux-router sysctl net.ipv4.ip_forward
docker exec linux-server ip route
```

Expected behavior:

- client routes `172.31.0.0/24` through `172.30.0.254`
- router has IP forwarding enabled
- server routes `172.30.0.0/24` through `172.31.0.254`

## Fault State Looks Wrong

Inspect the configured impairment interface:

```bash
docker exec linux-router tc qdisc show dev eth1
```

Clear it manually:

```bash
docker exec linux-router sh -lc 'tc qdisc del dev eth1 root 2>/dev/null || true'
```

## Throughput Is Lower Than Expected

Throughput in this lab is affected by host load and Docker networking overhead. Re-run the baseline
scenario before adjusting thresholds. If the baseline is consistently low, inspect host CPU load and
ensure no other heavy network tests are running.

## Report Generation Fails

Confirm `reports/results.json` exists:

```bash
ls -l reports/results.json
uv run netlab report --input reports/results.json --output reports/example_report.html
```
