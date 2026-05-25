from __future__ import annotations

from pathlib import Path

from netlab_validator.command_runner import CommandResult
from netlab_validator.config import load_scenario
from netlab_validator.testsuite import run_scenario


class FakeRunner:
    def __init__(self) -> None:
        self.commands: list[tuple[str, list[str]]] = []

    def exec(
        self,
        container: str,
        args: list[str],
        *,
        check: bool = True,
        timeout: int | None = None,
    ) -> CommandResult:
        self.commands.append((container, args))
        rendered = " ".join(args)
        if "ping" in rendered:
            stdout = (
                "5 packets transmitted, 5 received, 0% packet loss, time 4095ms\n"
                "rtt min/avg/max/mdev = 0.052/0.078/0.118/0.023 ms\n"
            )
        elif "iperf3" in rendered:
            stdout = (
                '{"end": {"sum_received": {"seconds": 3.0, '
                '"bits_per_second": 500000000.0, "retransmits": 0}}}'
            )
        elif "traceroute" in rendered:
            stdout = (
                "traceroute to 172.31.0.10 (172.31.0.10), 5 hops max\n"
                " 1  172.30.0.254  0.123 ms\n"
                " 2  172.31.0.10  0.211 ms\n"
            )
        else:
            stdout = ""
        return CommandResult(
            command=["docker", "exec", container, *args],
            returncode=0,
            stdout=stdout,
            stderr="",
            elapsed_seconds=0.01,
        )


def test_run_scenario_orchestrates_fault_and_validates_results(tmp_path: Path) -> None:
    scenario = load_scenario("configs/packet_loss.yaml")
    runner = FakeRunner()

    results = run_scenario(scenario, runner, output_dir=tmp_path)

    assert results["status"] == "pass"
    assert results["test_results"]["ping"]["packet_loss_percent"] == 0.0
    assert results["test_results"]["iperf3"]["throughput_mbps"] == 500.0
    assert results["test_results"]["traceroute"]["hops"] == ["172.30.0.254", "172.31.0.10"]
    assert any("netem loss 10%" in " ".join(args) for _, args in runner.commands)
    cleanup_commands = [
        args for _, args in runner.commands if "tc qdisc del dev eth1 root" in " ".join(args)
    ]
    assert len(cleanup_commands) == 2
