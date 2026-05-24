from __future__ import annotations

from dataclasses import dataclass

from netlab_validator.command_runner import CommandResult, CommandRunner


@dataclass(frozen=True)
class Topology:
    client: str = "linux-client"
    router: str = "linux-router"
    server: str = "linux-server"
    client_network: str = "172.30.0.0/24"
    server_network: str = "172.31.0.0/24"
    router_client_ip: str = "172.30.0.254"
    router_server_ip: str = "172.31.0.254"
    server_ip: str = "172.31.0.10"


def compose_up(runner: CommandRunner) -> CommandResult:
    return runner.compose(["up", "-d", "--build"], timeout=180)


def compose_down(runner: CommandRunner) -> CommandResult:
    return runner.compose(["down"], timeout=120)


def compose_ps(runner: CommandRunner) -> CommandResult:
    return runner.compose(["ps"])
