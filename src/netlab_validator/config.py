from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field, model_validator


class TargetConfig(BaseModel):
    host: str
    expected_hops: list[str] = Field(default_factory=list)


class FaultConfig(BaseModel):
    enabled: bool = False
    interface: str = "eth1"
    delay_ms: float | None = Field(default=None, ge=0)
    loss_percent: float | None = Field(default=None, ge=0, le=100)
    bandwidth_mbit: float | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_enabled_fault(self) -> FaultConfig:
        if self.enabled and not any(
            value is not None for value in (self.delay_ms, self.loss_percent, self.bandwidth_mbit)
        ):
            raise ValueError("enabled fault configuration must define delay, loss, or bandwidth")
        return self


class PingConfig(BaseModel):
    count: int = Field(default=5, ge=1)
    timeout_seconds: int = Field(default=2, ge=1)


class IperfConfig(BaseModel):
    duration_seconds: int = Field(default=3, ge=1)
    reverse: bool = False


class TracerouteConfig(BaseModel):
    max_hops: int = Field(default=5, ge=1)


class TestConfig(BaseModel):
    ping: PingConfig = Field(default_factory=PingConfig)
    iperf3: IperfConfig = Field(default_factory=IperfConfig)
    traceroute: TracerouteConfig = Field(default_factory=TracerouteConfig)


class ThresholdConfig(BaseModel):
    max_avg_latency_ms: float = Field(ge=0)
    max_packet_loss_percent: float = Field(ge=0, le=100)
    min_throughput_mbps: float = Field(ge=0)
    max_throughput_mbps: float | None = Field(default=None, ge=0)
    require_expected_hops: bool = True


class CaptureConfig(BaseModel):
    enabled: bool = False
    interface: str = "eth0"
    duration_seconds: int = Field(default=10, ge=1)


class ScenarioConfig(BaseModel):
    name: str = Field(min_length=1)
    description: str
    target: TargetConfig
    fault: FaultConfig = Field(default_factory=FaultConfig)
    tests: TestConfig = Field(default_factory=TestConfig)
    thresholds: ThresholdConfig
    capture: CaptureConfig = Field(default_factory=CaptureConfig)


def load_scenario(path: str | Path) -> ScenarioConfig:
    scenario_path = Path(path)
    with scenario_path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    if not isinstance(raw, dict):
        raise ValueError(f"Scenario file must contain a YAML mapping: {scenario_path}")
    return ScenarioConfig.model_validate(raw)
