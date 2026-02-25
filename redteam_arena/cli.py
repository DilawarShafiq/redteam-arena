"""
RedTeam Arena CLI -- AI vs AI security battles.
Entry point for the `redteam-arena` command.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys

import click

from redteam_arena.agents.claude_adapter import ClaudeAdapter, validate_api_key
from redteam_arena.agents.red_agent import RedAgent
from redteam_arena.agents.blue_agent import BlueAgent
from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
from redteam_arena.display import (
    display_battle_header,
    display_battle_summary,
    display_report_path,
    display_error,
    display_no_findings,
    display_interrupted,
)
from redteam_arena.reports.battle_report import generate_report, write_report
from redteam_arena.scenarios.scenario import load_scenario, list_scenarios
from redteam_arena.types import BattleConfig, BattleSummary, Scenario


@click.group()
@click.version_option("0.1.0", prog_name="redteam-arena")
def cli() -> None:
    """AI vs AI adversarial security testing. Red team attacks, blue team defends."""


@cli.command()
@click.argument("directory")
@click.option(
    "-s",
    "--scenario",
    "scenario_name",
    required=True,
    help="Scenario name (e.g., sql-injection, xss, full-audit)",
)
@click.option(
    "-r",
    "--rounds",
    default=5,
    type=int,
    help="Number of battle rounds",
    show_default=True,
)
def battle(directory: str, scenario_name: str, rounds: int) -> None:
    """Start a security battle against a target codebase."""
    try:
        asyncio.run(_battle_async(directory, scenario_name, rounds))
    except SystemExit:
        raise
    except Exception as err:
        display_error(str(err))
        sys.exit(1)


async def _battle_async(directory: str, scenario_name: str, rounds: int) -> None:
    """Async implementation of the battle command."""
    # Pre-flight: API key
    if not validate_api_key():
        display_error(
            "ANTHROPIC_API_KEY environment variable is required.\n"
            "  Get your key at https://console.anthropic.com/"
        )
        sys.exit(2)

    # Pre-flight: directory exists
    target_dir = os.path.abspath(directory)
    if not os.path.isdir(target_dir):
        display_error(f"Directory not found: {target_dir}")
        sys.exit(2)

    # Pre-flight: scenario
    scenario_result = await load_scenario(scenario_name)
    if not scenario_result.ok:
        available = await list_scenarios()
        names = ", ".join(s.name for s in available)
        display_error(
            f"Unknown scenario '{scenario_name}'. Available scenarios: {names}"
        )
        sys.exit(2)

    scenario = scenario_result.value

    # Handle meta-scenarios (full-audit)
    if scenario.is_meta and scenario.sub_scenarios:
        await _run_meta_battle(target_dir, scenario, rounds)
    else:
        await _run_battle(target_dir, scenario, rounds)


async def _run_battle(target_dir: str, scenario: Scenario, rounds: int) -> None:
    """Run a single battle."""
    provider = ClaudeAdapter()
    red_agent = RedAgent(provider)
    blue_agent = BlueAgent(provider)

    config = BattleConfig(
        target_dir=target_dir,
        scenario=scenario,
        rounds=rounds,
    )

    engine = BattleEngine(
        BattleEngineOptions(
            red_agent=red_agent,
            blue_agent=blue_agent,
            config=config,
        )
    )

    # SIGINT handling
    def sigint_handler(signum: int, frame: object) -> None:
        engine.interrupt()
        display_interrupted()

    original_handler = signal.getsignal(signal.SIGINT)
    signal.signal(signal.SIGINT, sigint_handler)

    display_battle_header(scenario.name, target_dir)

    battle_result = await engine.run()

    signal.signal(signal.SIGINT, original_handler)

    # Summary
    all_findings = [f for r in battle_result.rounds for f in r.findings]
    all_mitigations = [m for r in battle_result.rounds for m in r.mitigations]

    if not all_findings:
        display_no_findings()
    else:
        summary = BattleSummary(
            total_rounds=len(battle_result.rounds),
            total_findings=len(all_findings),
            findings_by_severity={
                "critical": sum(1 for f in all_findings if f.severity == "critical"),
                "high": sum(1 for f in all_findings if f.severity == "high"),
                "medium": sum(1 for f in all_findings if f.severity == "medium"),
                "low": sum(1 for f in all_findings if f.severity == "low"),
            },
            total_mitigations=len(all_mitigations),
            mitigation_coverage=(
                len(all_mitigations) / len(all_findings)
                if all_findings
                else 1.0
            ),
        )

        display_battle_summary(summary)

        report_content = generate_report(battle_result)
        report_path = await write_report(report_content, battle_result.id)
        display_report_path(report_path)

    if battle_result.status == "error":
        sys.exit(1)
    if battle_result.status == "interrupted":
        sys.exit(1)


async def _run_meta_battle(
    target_dir: str, meta_scenario: Scenario, rounds: int
) -> None:
    """Run a meta-scenario (e.g., full-audit) that chains sub-scenarios."""
    click.echo(f"\n  Running full audit: {' -> '.join(meta_scenario.sub_scenarios)}\n")

    for sub_name in meta_scenario.sub_scenarios:
        sub_result = await load_scenario(sub_name)
        if sub_result.ok:
            click.echo(f"\n  --- Starting {sub_name} audit ---\n")
            await _run_battle(target_dir, sub_result.value, rounds)


@cli.command("list")
def list_cmd() -> None:
    """List all available scenarios."""
    asyncio.run(_list_async())


async def _list_async() -> None:
    """Async implementation of the list command."""
    scenarios = await list_scenarios()

    click.echo("\nAvailable Scenarios:\n")
    for s in scenarios:
        name = s.name.ljust(20)
        click.echo(f"  {name}{s.description}")
    click.echo("\nUsage: redteam-arena battle <directory> --scenario <name>\n")


if __name__ == "__main__":
    cli()
