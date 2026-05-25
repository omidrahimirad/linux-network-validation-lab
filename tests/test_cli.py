from __future__ import annotations

import pytest
from typer.testing import CliRunner

from netlab_validator import cli
from netlab_validator.command_runner import CommandExecutionError, CommandResult

runner = CliRunner()


def test_cli_help_lists_operational_commands() -> None:
    result = runner.invoke(cli.app, ["--help"])

    assert result.exit_code == 0
    assert "Linux network validation lab controller" in result.output
    assert "run" in result.output
    assert "report" in result.output


def test_cli_up_reports_compose_failure_without_traceback(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail_up(_: object) -> CommandResult:
        raise CommandExecutionError(
            CommandResult(
                command=["docker", "compose", "up", "-d", "--build"],
                returncode=1,
                stdout="",
                stderr="Cannot connect to the Docker daemon",
                elapsed_seconds=0.1,
            )
        )

    monkeypatch.setattr(cli, "compose_up", fail_up)

    result = runner.invoke(cli.app, ["up"])

    assert result.exit_code == 1
    assert "Command failed with exit code 1" in result.output
    assert "Cannot connect to the Docker daemon" in result.output
    assert "Traceback" not in result.output
