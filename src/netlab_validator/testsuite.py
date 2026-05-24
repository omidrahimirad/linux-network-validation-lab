from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from netlab_validator.command_runner import CommandExecutionError, CommandResult, CommandRunner
from netlab_validator.config import ScenarioConfig
from netlab_validator.fault_injection import (
    build_fault_command,
    describe_fault,
    reset_fault_command,
)
from netlab_validator.metrics import parse_iperf3_json, parse_ping, parse_traceroute
from netlab_validator.topology import Topology
from netlab_validator.validation import overall_status, validate_results


def _record(result: CommandResult) -> dict[str, object]:
    return result.summary()


def _run_capture_start(
    runner: CommandRunner,
    scenario: ScenarioConfig,
    topology: Topology,
) -> CommandResult | None:
    if not scenario.capture.enabled:
        return None
    capture_file = f"/captures/{scenario.name}.pcap"
    command = (
        f"timeout {scenario.capture.duration_seconds} tcpdump "
        f"-i {scenario.capture.interface} -w {capture_file} host {scenario.target.host} "
        ">/tmp/netlab-tcpdump.log 2>&1 &"
    )
    return runner.exec(topology.client, ["sh", "-lc", command], check=False)


def run_scenario(
    scenario: ScenarioConfig,
    runner: CommandRunner,
    *,
    output_dir: Path = Path("reports"),
    topology: Topology | None = None,
) -> dict[str, object]:
    active_topology = topology or Topology()
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "captures").mkdir(parents=True, exist_ok=True)

    raw_commands: list[dict[str, object]] = []
    fault_commands: list[str] = []

    reset = reset_fault_command(scenario.fault.interface, router=active_topology.router)
    reset_result = runner.exec(reset.container, reset.argv, check=False)
    raw_commands.append(_record(reset_result))
    fault_commands.append(reset.display)

    apply_fault = build_fault_command(scenario.fault, router=active_topology.router)
    if apply_fault is not None:
        apply_result = runner.exec(apply_fault.container, apply_fault.argv)
        raw_commands.append(_record(apply_result))
        fault_commands.append(apply_fault.display)

    capture_result = _run_capture_start(runner, scenario, active_topology)
    if capture_result is not None:
        raw_commands.append(_record(capture_result))

    ping_result = runner.exec(
        active_topology.client,
        [
            "ping",
            "-c",
            str(scenario.tests.ping.count),
            "-W",
            str(scenario.tests.ping.timeout_seconds),
            scenario.target.host,
        ],
        check=False,
        timeout=scenario.tests.ping.count * (scenario.tests.ping.timeout_seconds + 1) + 5,
    )
    raw_commands.append(_record(ping_result))
    try:
        ping = parse_ping(ping_result.stdout + ping_result.stderr)
    except ValueError as exc:
        raise CommandExecutionError(ping_result) from exc

    iperf_args = [
        "iperf3",
        "-c",
        scenario.target.host,
        "-t",
        str(scenario.tests.iperf3.duration_seconds),
        "-J",
    ]
    if scenario.tests.iperf3.reverse:
        iperf_args.append("--reverse")
    iperf_result = runner.exec(
        active_topology.client,
        iperf_args,
        timeout=scenario.tests.iperf3.duration_seconds + 15,
    )
    raw_commands.append(_record(iperf_result))
    iperf = parse_iperf3_json(iperf_result.stdout)

    traceroute_result = runner.exec(
        active_topology.client,
        ["traceroute", "-n", "-m", str(scenario.tests.traceroute.max_hops), scenario.target.host],
        check=False,
        timeout=20,
    )
    raw_commands.append(_record(traceroute_result))
    try:
        traceroute = parse_traceroute(traceroute_result.stdout + traceroute_result.stderr)
    except ValueError as exc:
        raise CommandExecutionError(traceroute_result) from exc

    checks = validate_results(scenario, ping, iperf, traceroute)
    status = overall_status(checks)

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scenario": scenario.model_dump(),
        "topology": active_topology.__dict__,
        "fault_injection": describe_fault(scenario.fault),
        "fault_commands": fault_commands,
        "test_results": {
            "ping": ping.__dict__,
            "iperf3": iperf.__dict__,
            "traceroute": traceroute.__dict__,
        },
        "validations": [check.__dict__ for check in checks],
        "status": status,
        "engineering_interpretation": _interpret(status, scenario.name),
        "troubleshooting_recommendations": _recommendations(status),
        "raw_commands": raw_commands,
    }


def _interpret(status: str, scenario_name: str) -> str:
    if status == "pass":
        return (
            f"Scenario '{scenario_name}' met the configured validation thresholds for this lab "
            "topology. Results should be interpreted as controlled container-lab evidence, not as "
            "a substitute for production network monitoring."
        )
    return (
        f"Scenario '{scenario_name}' did not meet one or more validation thresholds. Inspect the "
        "failed checks and raw command output before changing thresholds or lab parameters."
    )


def _recommendations(status: str) -> list[str]:
    if status == "pass":
        return [
            "Keep the scenario file with the report so thresholds remain auditable.",
            "Repeat the run after Docker or host networking changes to confirm reproducibility.",
        ]
    return [
        "Confirm the Docker topology is healthy with 'docker compose ps'.",
        "Inspect active qdisc state on linux-router with 'tc qdisc show dev eth1'.",
        "Use optional tcpdump capture when packet loss or route asymmetry is suspected.",
    ]
