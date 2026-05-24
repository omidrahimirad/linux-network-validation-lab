from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    elapsed_seconds: float

    def summary(self) -> dict[str, object]:
        return {
            "command": " ".join(self.command),
            "returncode": self.returncode,
            "elapsed_seconds": round(self.elapsed_seconds, 3),
            "stdout": self.stdout.strip(),
            "stderr": self.stderr.strip(),
        }


class CommandExecutionError(RuntimeError):
    def __init__(self, result: CommandResult) -> None:
        self.result = result
        super().__init__(
            f"Command failed with exit code {result.returncode}: {' '.join(result.command)}"
        )


class CommandRunner:
    def __init__(self, cwd: Path | None = None) -> None:
        self.cwd = cwd or Path.cwd()

    def run(
        self,
        command: list[str],
        *,
        check: bool = True,
        timeout: int | None = None,
    ) -> CommandResult:
        started = time.monotonic()
        completed = subprocess.run(
            command,
            cwd=self.cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        result = CommandResult(
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            elapsed_seconds=time.monotonic() - started,
        )
        if check and result.returncode != 0:
            raise CommandExecutionError(result)
        return result

    def compose(
        self,
        args: list[str],
        *,
        check: bool = True,
        timeout: int | None = None,
    ) -> CommandResult:
        return self.run(["docker", "compose", *args], check=check, timeout=timeout)

    def exec(
        self,
        container: str,
        args: list[str],
        *,
        check: bool = True,
        timeout: int | None = None,
    ) -> CommandResult:
        return self.run(["docker", "exec", container, *args], check=check, timeout=timeout)
