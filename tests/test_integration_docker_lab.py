from __future__ import annotations

import json
import subprocess
from collections.abc import Iterator

import pytest

pytestmark = pytest.mark.integration


def run_command(command: list[str], *, timeout: int = 60) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=True, timeout=timeout)


@pytest.fixture(scope="module", autouse=True)
def compose_lab() -> Iterator[None]:
    run_command(["docker", "compose", "up", "-d", "--build"], timeout=180)
    try:
        yield
    finally:
        subprocess.run(
            ["docker", "compose", "down"],
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )


def test_compose_services_are_running() -> None:
    result = run_command(["docker", "compose", "ps", "--format", "json"])

    services = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    observed = {service["Service"]: service["State"] for service in services}

    assert observed["linux-client"] == "running"
    assert observed["linux-router"] == "running"
    assert observed["linux-server"] == "running"


def test_client_reaches_server_with_linux_tools() -> None:
    ping = run_command(
        ["docker", "compose", "exec", "-T", "linux-client", "ping", "-c", "5", "linux-server"]
    )
    iperf = run_command(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "linux-client",
            "iperf3",
            "-c",
            "linux-server",
            "-J",
            "-t",
            "5",
        ]
    )
    traceroute = run_command(
        ["docker", "compose", "exec", "-T", "linux-client", "traceroute", "linux-server"]
    )

    assert "0% packet loss" in ping.stdout
    assert json.loads(iperf.stdout)["end"]["sum_received"]["bits_per_second"] > 0
    assert "linux-server" in traceroute.stdout or "172.31.0.10" in traceroute.stdout
