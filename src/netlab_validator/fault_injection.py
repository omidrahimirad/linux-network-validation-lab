from __future__ import annotations

from dataclasses import dataclass

from netlab_validator.config import FaultConfig


@dataclass(frozen=True)
class FaultCommand:
    container: str
    argv: list[str]
    description: str

    @property
    def display(self) -> str:
        return " ".join(["docker", "exec", self.container, *self.argv])


def reset_fault_command(interface: str, *, router: str = "linux-router") -> FaultCommand:
    return FaultCommand(
        container=router,
        argv=["sh", "-lc", f"tc qdisc del dev {interface} root 2>/dev/null || true"],
        description=f"clear tc qdisc on {interface}",
    )


def build_fault_command(fault: FaultConfig, *, router: str = "linux-router") -> FaultCommand | None:
    if not fault.enabled:
        return None

    netem_parts = ["tc", "qdisc", "replace", "dev", fault.interface, "root", "netem"]
    if fault.delay_ms is not None:
        netem_parts.extend(["delay", f"{fault.delay_ms:g}ms"])
    if fault.loss_percent is not None:
        netem_parts.extend(["loss", f"{fault.loss_percent:g}%"])
    if fault.bandwidth_mbit is not None:
        netem_parts.extend(["rate", f"{fault.bandwidth_mbit:g}mbit"])

    return FaultCommand(
        container=router,
        argv=["sh", "-lc", " ".join(netem_parts)],
        description=f"apply tc/netem impairment on {fault.interface}",
    )


def describe_fault(fault: FaultConfig) -> dict[str, object]:
    return {
        "enabled": fault.enabled,
        "interface": fault.interface,
        "delay_ms": fault.delay_ms,
        "loss_percent": fault.loss_percent,
        "bandwidth_mbit": fault.bandwidth_mbit,
    }
