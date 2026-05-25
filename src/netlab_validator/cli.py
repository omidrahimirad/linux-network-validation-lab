from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from netlab_validator.command_runner import CommandExecutionError, CommandRunner
from netlab_validator.config import load_scenario
from netlab_validator.logging_config import configure_logging
from netlab_validator.reporting import (
    generate_html_report,
    load_results,
    merge_result_archive,
    write_results_csv,
    write_results_json,
)
from netlab_validator.testsuite import run_scenario
from netlab_validator.topology import compose_down, compose_ps, compose_up

app = typer.Typer(help="Linux network validation lab controller.")
console = Console()


def _print_command_error(exc: CommandExecutionError) -> None:
    console.print(f"[red]{exc}[/red]")
    if exc.result.stderr:
        console.print(exc.result.stderr)


@app.callback()
def main(
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable debug logging."),
    ] = False,
) -> None:
    configure_logging(verbose)


@app.command()
def up() -> None:
    """Build and start the Docker Compose lab."""
    try:
        result = compose_up(CommandRunner())
    except CommandExecutionError as exc:
        _print_command_error(exc)
        raise typer.Exit(code=exc.result.returncode) from exc
    console.print(result.stdout.strip() or "Lab started.")


@app.command()
def down() -> None:
    """Stop and remove the Docker Compose lab."""
    try:
        result = compose_down(CommandRunner())
    except CommandExecutionError as exc:
        _print_command_error(exc)
        raise typer.Exit(code=exc.result.returncode) from exc
    console.print(result.stdout.strip() or "Lab stopped.")


@app.command("ps")
def ps() -> None:
    """Show Docker Compose service state."""
    try:
        result = compose_ps(CommandRunner())
    except CommandExecutionError as exc:
        _print_command_error(exc)
        raise typer.Exit(code=exc.result.returncode) from exc
    console.print(result.stdout)


@app.command("run")
def run_command(
    scenario: Annotated[
        Path,
        typer.Option("--scenario", "-s", help="Path to scenario YAML."),
    ],
    output_dir: Annotated[
        Path,
        typer.Option("--output-dir", help="Directory for run outputs."),
    ] = Path("reports"),
) -> None:
    """Run the validation tests for a scenario."""
    try:
        scenario_config = load_scenario(scenario)
        results = run_scenario(scenario_config, CommandRunner(), output_dir=output_dir)
    except CommandExecutionError as exc:
        _print_command_error(exc)
        raise typer.Exit(code=exc.result.returncode) from exc

    json_path = output_dir / "results.json"
    csv_path = output_dir / "results.csv"
    existing_results = load_results(json_path) if json_path.exists() else None
    archived_results = merge_result_archive(existing_results, results)
    write_results_json(archived_results, json_path)
    write_results_csv(archived_results, csv_path)
    console.print(f"Scenario: {scenario_config.name}")
    console.print(f"Status: {results['status']}")
    console.print(f"Wrote {json_path} and {csv_path}")
    if results["status"] != "pass":
        raise typer.Exit(code=2)


@app.command()
def report(
    input: Annotated[Path, typer.Option("--input", "-i", help="Input results JSON.")],
    output: Annotated[Path, typer.Option("--output", "-o", help="Output HTML report.")],
) -> None:
    """Generate an HTML report from a results JSON file."""
    results = load_results(input)
    generate_html_report(results, output)
    console.print(f"Wrote {output}")
