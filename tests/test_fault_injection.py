from __future__ import annotations

from netlab_validator.config import FaultConfig
from netlab_validator.fault_injection import build_fault_command, reset_fault_command


def test_reset_fault_command() -> None:
    command = reset_fault_command("eth1")

    assert command.container == "linux-router"
    assert "tc qdisc del dev eth1 root" in command.argv[-1]


def test_build_delay_loss_rate_command() -> None:
    command = build_fault_command(
        FaultConfig(
            enabled=True,
            interface="eth1",
            delay_ms=50,
            loss_percent=2.5,
            bandwidth_mbit=10,
        )
    )

    assert command is not None
    rendered = command.argv[-1]
    assert "tc qdisc replace dev eth1 root netem" in rendered
    assert "delay 50ms" in rendered
    assert "loss 2.5%" in rendered
    assert "rate 10mbit" in rendered


def test_disabled_fault_has_no_apply_command() -> None:
    assert build_fault_command(FaultConfig(enabled=False)) is None
