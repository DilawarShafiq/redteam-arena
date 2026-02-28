"""
RedTeam Arena CLI -- AI vs AI security battles.
Entry point for the `redteam-arena` command.
7 commands: battle, list, serve, watch, benchmark, history, dashboard.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys

import click

from redteam_arena.display import (
    display_battle_header,
    display_battle_summary,
    display_error,
    display_interrupted,
    display_no_findings,
    display_report_path,
    display_warning,
)
from redteam_arena.types import BattleConfig, BattleSummary, Scenario

# --- Helpers ---


def _severity_order() -> dict[str, int]:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _should_fail(findings: list, fail_on: str | None) -> bool:
    """Check if any findings meet the fail-on threshold."""
    if not fail_on:
        return False
    order = _severity_order()
    threshold = order.get(fail_on, 99)
    return any(order.get(f.severity, 99) <= threshold for f in findings)


# --- CLI Group ---


@click.group()
@click.version_option("0.0.4", prog_name="redteam-arena")
def cli() -> None:
    """AI vs AI adversarial security testing. Red team attacks, blue team defends."""


# --- Battle Command ---


@cli.command()
@click.argument("directory")
@click.option("-s", "--scenario", "scenario_name", required=True, help="Scenario name")
@click.option("-r", "--rounds", default=5, type=int, show_default=True, help="Number of battle rounds")
@click.option("-p", "--provider", default=None, help="LLM provider (claude, openai, gemini, ollama)")
@click.option("-m", "--model", default=None, help="Specific model to use")
@click.option("-f", "--format", "report_format", default=None, type=click.Choice(["markdown", "json", "sarif", "html", "compliance"]), help="Report format")
@click.option("-o", "--output", default=None, help="Output file path")
@click.option("--diff/--no-diff", default=False, help="Only scan changed files (git diff)")
@click.option("--diff-base", default="HEAD~1", show_default=True, help="Git ref for diff base")
@click.option("--auto-fix/--no-auto-fix", default=False, help="Generate fix branches")
@click.option("--auto-fix-dry-run", is_flag=True, default=False, help="Preview fixes without applying")
@click.option("--fail-on", default=None, type=click.Choice(["critical", "high", "medium", "low"]), help="Exit non-zero if severity found")
@click.option("--analyze/--no-analyze", default=False, help="Run advanced analysis")
@click.option("--tag", multiple=True, help="Filter scenarios by tag")
@click.option("--exclude-tag", multiple=True, help="Exclude scenarios by tag")
@click.option("--scenario-dir", default=None, help="Custom scenario directory")
@click.option("--pr-comment/--no-pr-comment", default=False, help="Post results as GitHub PR comment")
@click.option("--agent-mode", default="attacker", type=click.Choice(["attacker", "auditor"]), help="Mode for the primary agent")
@click.option("--mock-llm", is_flag=True, default=False, help="Use a mock LLM for testing/demo")
def battle(
    directory: str,
    scenario_name: str,
    rounds: int,
    provider: str | None,
    model: str | None,
    report_format: str | None,
    output: str | None,
    diff: bool,
    diff_base: str,
    auto_fix: bool,
    auto_fix_dry_run: bool,
    fail_on: str | None,
    analyze: bool,
    tag: tuple[str, ...],
    exclude_tag: tuple[str, ...],
    scenario_dir: str | None,
    pr_comment: bool,
    agent_mode: str,
    mock_llm: bool,
) -> None:
    """Start a security battle against a target codebase."""
    try:
        asyncio.run(
            _battle_async(
                directory=directory,
                scenario_name=scenario_name,
                rounds=rounds,
                provider_id=provider,
                model=model,
                report_format=report_format or "markdown",
                output_path=output or "",
                diff_only=diff,
                diff_base=diff_base,
                auto_fix=auto_fix,
                auto_fix_dry_run=auto_fix_dry_run,
                fail_on=fail_on,
                do_analyze=analyze,
                tags=list(tag),
                exclude_tags=list(exclude_tag),
                scenario_dir=scenario_dir or "",
                pr_comment=pr_comment,
                agent_mode=agent_mode,
                mock_llm=mock_llm,
            )
        )
    except SystemExit:
        raise
    except Exception as err:
        display_error(str(err))
        sys.exit(1)


async def _battle_async(
    *,
    directory: str,
    scenario_name: str,
    rounds: int,
    provider_id: str | None,
    model: str | None,
    report_format: str,
    output_path: str,
    diff_only: bool,
    diff_base: str,
    auto_fix: bool,
    auto_fix_dry_run: bool,
    fail_on: str | None,
    do_analyze: bool,
    tags: list[str],
    exclude_tags: list[str],
    scenario_dir: str,
    pr_comment: bool,
    agent_mode: str,
    mock_llm: bool,
) -> None:
    """Full async battle implementation."""
    from redteam_arena.agents.provider_registry import (
        detect_provider,
        validate_provider,
    )
    from redteam_arena.core.config import load_config
    from redteam_arena.scenarios.scenario import list_scenarios, load_scenario

    # Load config file
    target_dir = os.path.abspath(directory)
    config_result = await load_config(target_dir)
    file_config = config_result.value if config_result.ok else None

    # Resolve provider
    resolved_provider = provider_id
    if not resolved_provider:
        if file_config and file_config.provider:
            resolved_provider = file_config.provider
        else:
            resolved_provider = detect_provider()

    valid, msg = validate_provider(resolved_provider)  # type: ignore[arg-type]
    if not valid:
        display_error(msg)
        sys.exit(2)

    # Pre-flight: directory exists
    if not os.path.isdir(target_dir):
        display_error(f"Directory not found: {target_dir}")
        sys.exit(2)

    # Pre-flight: scenario
    scenario_result = await load_scenario(scenario_name, scenario_dir=scenario_dir)
    if not scenario_result.ok:
        available = await list_scenarios()
        names = ", ".join(s.name for s in available)
        display_error(f"Unknown scenario '{scenario_name}'. Available: {names}")
        sys.exit(2)

    scenario = scenario_result.value

    # Resolve model
    resolved_model = model or (file_config.model if file_config else None) or ""

    # Handle meta-scenarios
    if scenario.is_meta and scenario.sub_scenarios:
        click.echo(f"\n  Running full audit: {' -> '.join(scenario.sub_scenarios)}\n")
        for sub_name in scenario.sub_scenarios:
            sub_result = await load_scenario(sub_name, scenario_dir=scenario_dir)
            if sub_result.ok:
                click.echo(f"\n  --- Starting {sub_name} audit ---\n")
                await _run_single_battle(
                    target_dir=target_dir,
                    scenario=sub_result.value,
                    rounds=rounds,
                    provider_id=resolved_provider,  # type: ignore[arg-type]
                    model=resolved_model,
                    report_format=report_format,
                    output_path=output_path,
                    diff_only=diff_only,
                    diff_base=diff_base,
                    auto_fix=auto_fix,
                    auto_fix_dry_run=auto_fix_dry_run,
                    fail_on=fail_on,
                    do_analyze=do_analyze,
                    pr_comment=pr_comment,
                    agent_mode=agent_mode,
                    mock_llm=mock_llm,
                )
        return

    await _run_single_battle(
        target_dir=target_dir,
        scenario=scenario,
        rounds=rounds,
        provider_id=resolved_provider,  # type: ignore[arg-type]
        model=resolved_model,
        report_format=report_format,
        output_path=output_path,
        diff_only=diff_only,
        diff_base=diff_base,
        auto_fix=auto_fix,
        auto_fix_dry_run=auto_fix_dry_run,
        fail_on=fail_on,
        do_analyze=do_analyze,
        pr_comment=pr_comment,
        agent_mode=agent_mode,
        mock_llm=mock_llm,
    )


async def _run_single_battle(
    *,
    target_dir: str,
    scenario: Scenario,
    rounds: int,
    provider_id: str,
    model: str,
    report_format: str,
    output_path: str,
    diff_only: bool,
    diff_base: str,
    auto_fix: bool,
    auto_fix_dry_run: bool,
    fail_on: str | None,
    do_analyze: bool,
    pr_comment: bool,
    agent_mode: str,
    mock_llm: bool,
) -> None:
    """Run a single battle with all options."""
    from redteam_arena.agents.blue_agent import BlueAgent
    from redteam_arena.agents.provider_registry import create_provider
    from redteam_arena.agents.red_agent import RedAgent
    from redteam_arena.agents.auditor_agent import AuditorAgent
    from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
    from redteam_arena.core.battle_store import BattleStore
    from redteam_arena.reports.battle_report import generate_report, write_report

    if mock_llm:
        from redteam_arena.agents.mock_provider import MockProvider
        provider = MockProvider()  # type: ignore[assignment]
    else:
        provider = create_provider(provider_id, model=model)  # type: ignore[arg-type]

    if agent_mode == "auditor":
        red_agent = AuditorAgent(provider, model=model)
    else:
        red_agent = RedAgent(provider, model=model)
    blue_agent = BlueAgent(provider, model=model)

    # Handle diff-only mode
    override_files = None
    if diff_only:
        from redteam_arena.core.diff_reader import read_diff_files
        diff_result = await read_diff_files(target_dir, base=diff_base)
        if diff_result.ok:
            override_files = diff_result.value
            if not override_files:
                click.echo("\n  No changed files found in diff. Nothing to scan.\n")
                return
            click.echo(f"\n  Scanning {len(override_files)} changed file(s) (diff from {diff_base})\n")
        else:
            display_warning(f"Diff failed, falling back to full scan: {diff_result.error}")

    config = BattleConfig(
        target_dir=target_dir,
        scenario=scenario,
        rounds=rounds,
        provider=provider_id,  # type: ignore[arg-type]
        model=model,
        format=report_format,  # type: ignore[arg-type]
    )

    engine = BattleEngine(
        BattleEngineOptions(
            red_agent=red_agent,
            blue_agent=blue_agent,
            config=config,
            override_files=override_files,
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

    if battle_result.status == "error":
        error_events = [e for e in battle_result.events if e.type == "error"]
        msg = error_events[0].message if error_events else "Unknown error"
        from redteam_arena.display import display_error
        display_error(f"Battle failed: {msg}")

    # Collect findings
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
                len(all_mitigations) / len(all_findings) if all_findings else 1.0
            ),
        )
        display_battle_summary(summary)

    # Generate report
    ext_map = {"markdown": "md", "json": "json", "sarif": "sarif.json", "html": "html", "compliance": "md"}
    extension = ext_map.get(report_format, "md")

    if report_format == "sarif":
        from redteam_arena.reports.sarif_reporter import generate_sarif_report
        report_content = generate_sarif_report(battle_result)
    elif report_format == "json":
        from redteam_arena.reports.sarif_reporter import generate_json_report
        report_content = generate_json_report(battle_result)
    elif report_format == "html":
        from redteam_arena.reports.html_reporter import generate_html_report
        report_content = generate_html_report(battle_result)
    elif report_format == "compliance":
        from redteam_arena.reports.compliance_reporter import generate_compliance_report
        report_content = generate_compliance_report(battle_result)
    else:
        from redteam_arena.reports.battle_report import generate_report
        report_content = generate_report(battle_result)

    if report_format == "compliance":
        from redteam_arena.reports.compliance_reporter import write_compliance_report
        report_path = await write_compliance_report(
            report_content, battle_result.id, output_path=output_path,
        )
    else:
        report_path = await write_report(
            report_content, battle_result.id, extension=extension, output_path=output_path,
        )
    display_report_path(report_path)

    # Save to battle store
    store = BattleStore()
    try:
        await store.save(battle_result)
    except Exception:
        pass  # Non-critical

    # Advanced analysis
    if do_analyze and all_findings:
        from redteam_arena.core.advanced_analysis import (
            format_advanced_analysis,
            run_advanced_analysis,
        )
        from redteam_arena.core.file_reader import read_codebase
        code_result = await read_codebase(target_dir)
        if code_result.ok:
            analysis = await run_advanced_analysis(code_result.value, all_findings)
            click.echo(format_advanced_analysis(analysis))

    # Auto-fix
    if (auto_fix or auto_fix_dry_run) and all_findings:
        from redteam_arena.core.auto_fix import format_auto_fix_summary, run_auto_fix
        fix_result = await run_auto_fix(
            target_dir, battle_result, dry_run=auto_fix_dry_run,
        )
        if fix_result.ok:
            click.echo(format_auto_fix_summary(fix_result.value))

    # PR comment
    if pr_comment:
        try:
            from redteam_arena.reports.pr_commenter import post_pr_comment
            await post_pr_comment(battle_result)
            click.echo("\n  PR comment posted successfully.\n")
        except Exception as exc:
            display_warning(f"Failed to post PR comment: {exc}")

    # Fail-on check
    if _should_fail(all_findings, fail_on):
        click.echo(f"\n  Failing: findings at {fail_on} severity or above.\n")
        sys.exit(1)

    if battle_result.status in ("error", "interrupted"):
        sys.exit(1)


# --- List Command ---


@cli.command("list")
@click.option("--tag", multiple=True, help="Filter by tag")
@click.option("--exclude-tag", multiple=True, help="Exclude by tag")
@click.option("--scenario-dir", default=None, help="Custom scenario directory")
def list_cmd(tag: tuple[str, ...], exclude_tag: tuple[str, ...], scenario_dir: str | None) -> None:
    """List all available scenarios."""
    asyncio.run(_list_async(list(tag), list(exclude_tag), scenario_dir or ""))


async def _list_async(tags: list[str], exclude_tags: list[str], scenario_dir: str) -> None:
    from redteam_arena.scenarios.scenario import list_scenarios
    scenarios = await list_scenarios(tags=tags or None, exclude_tags=exclude_tags or None, scenario_dir=scenario_dir)

    click.echo("\nAvailable Scenarios:\n")
    for s in scenarios:
        name = s.name.ljust(30)
        tag_str = f" [{', '.join(s.tags)}]" if s.tags else ""
        click.echo(f"  {name}{s.description}{tag_str}")
    click.echo(f"\n  {len(scenarios)} scenario(s) available.")
    click.echo("  Usage: redteam-arena battle <directory> --scenario <name>\n")


# --- Serve Command ---


@cli.command()
@click.option("--host", default="0.0.0.0", show_default=True, help="Server host")
@click.option("--port", default=3000, type=int, show_default=True, help="Server port")
def serve(host: str, port: int) -> None:
    """Start the API server (requires [server] extras)."""
    try:
        from redteam_arena.server.api_server import start_server
        click.echo(f"\n  Starting RedTeam Arena API server on {host}:{port}\n")
        start_server(host=host, port=port)
    except ImportError as exc:
        display_error(f"Server dependencies missing: {exc}\n  Install with: pip install redteam-arena[server]")
        sys.exit(1)


# --- Watch Command ---


@cli.command()
@click.argument("directory")
@click.option("-s", "--scenario", "scenario_name", required=True, help="Scenario name")
@click.option("-r", "--rounds", default=3, type=int, show_default=True, help="Rounds per scan")
@click.option("-p", "--provider", default=None, help="LLM provider")
@click.option("-m", "--model", default=None, help="Model name")
def watch(directory: str, scenario_name: str, rounds: int, provider: str | None, model: str | None) -> None:
    """Watch a directory for changes and re-scan automatically."""
    asyncio.run(_watch_async(directory, scenario_name, rounds, provider, model))


async def _watch_async(
    directory: str, scenario_name: str, rounds: int,
    provider_id: str | None, model: str | None,
) -> None:
    from redteam_arena.agents.provider_registry import detect_provider
    from redteam_arena.core.watcher import WatchMode
    from redteam_arena.scenarios.scenario import load_scenario

    target_dir = os.path.abspath(directory)
    if not os.path.isdir(target_dir):
        display_error(f"Directory not found: {target_dir}")
        sys.exit(2)

    scenario_result = await load_scenario(scenario_name)
    if not scenario_result.ok:
        display_error(f"Unknown scenario: {scenario_name}")
        sys.exit(2)

    resolved_provider = provider_id or detect_provider()

    watcher = WatchMode(
        target_dir=target_dir,
        scenario=scenario_result.value,
        rounds=rounds,
        provider_id=resolved_provider,  # type: ignore[arg-type]
        model=model or "",
    )

    watcher.start()

    try:
        while watcher.running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()


# --- Benchmark Command ---


@cli.command()
@click.option("--suite", default="owasp-web-basic", show_default=True, help="Benchmark suite name")
@click.option("-p", "--provider", default=None, help="LLM provider")
@click.option("-m", "--model", default=None, help="Model name")
@click.option("--list-suites", is_flag=True, default=False, help="List available suites")
def benchmark(suite: str, provider: str | None, model: str | None, list_suites: bool) -> None:
    """Run detection accuracy benchmarks."""
    if list_suites:
        from redteam_arena.core.benchmark import list_benchmark_suites
        suites = list_benchmark_suites()
        click.echo("\nAvailable Benchmark Suites:\n")
        for s in suites:
            click.echo(f"  {str(s['name']).ljust(25)}{s['patterns']} patterns, {s['categories']} categories")
        click.echo()
        return

    asyncio.run(_benchmark_async(suite, provider, model))


async def _benchmark_async(suite_name: str, provider_id: str | None, model: str | None) -> None:
    from redteam_arena.agents.blue_agent import BlueAgent
    from redteam_arena.agents.provider_registry import create_provider, detect_provider
    from redteam_arena.agents.red_agent import RedAgent
    from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
    from redteam_arena.core.benchmark import (
        create_benchmark_files,
        evaluate_results,
        format_benchmark_result,
        get_benchmark_suite,
    )
    from redteam_arena.scenarios.scenario import load_scenario

    patterns = get_benchmark_suite(suite_name)
    if not patterns:
        display_error(f"Unknown suite: {suite_name}")
        sys.exit(2)

    click.echo(f"\n  Running benchmark: {suite_name} ({len(patterns)} patterns)\n")

    temp_dir, _ = create_benchmark_files(patterns)

    resolved_provider = provider_id or detect_provider()
    resolved_model = model or ""
    provider = create_provider(resolved_provider, model=resolved_model)  # type: ignore[arg-type]

    scenario_result = await load_scenario("full-audit")
    scenario = scenario_result.value if scenario_result.ok else None
    if not scenario:
        display_error("full-audit scenario not found")
        sys.exit(2)

    red_agent = RedAgent(provider, model=resolved_model)
    blue_agent = BlueAgent(provider, model=resolved_model)

    config = BattleConfig(target_dir=temp_dir, scenario=scenario, rounds=1)
    engine = BattleEngine(BattleEngineOptions(red_agent=red_agent, blue_agent=blue_agent, config=config))
    battle_result = await engine.run()

    all_findings = [f for r in battle_result.rounds for f in r.findings]
    result = evaluate_results(patterns, all_findings)
    result.suite_name = suite_name
    click.echo(format_benchmark_result(result))

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


# --- History Command ---


@cli.command()
@click.option("--scenario", default=None, help="Filter by scenario")
@click.option("--limit", default=20, type=int, show_default=True, help="Max records")
@click.option("--trends", is_flag=True, default=False, help="Show daily trends")
@click.option("--regression", is_flag=True, default=False, help="Show regression analysis")
@click.option("--target", default=None, help="Target directory for trends/regression")
def history(scenario: str | None, limit: int, trends: bool, regression: bool, target: str | None) -> None:
    """View battle history and trends."""
    asyncio.run(_history_async(scenario, limit, trends, regression, target))


async def _history_async(
    scenario: str | None, limit: int, show_trends: bool, show_regression: bool, target: str | None,
) -> None:
    from redteam_arena.core.battle_store import BattleQuery, BattleStore

    store = BattleStore()

    if show_trends:
        target_dir = target or os.getcwd()
        trend_data = await store.get_trends(target_dir)
        if not trend_data:
            click.echo("\n  No trend data available.\n")
            return
        click.echo("\n  Battle Trends\n  " + "=" * 40)
        for t in trend_data:
            click.echo(
                f"  {t.period}: {t.total_battles} battles, "
                f"{t.total_findings} findings, "
                f"{round(t.avg_coverage * 100)}% coverage"
            )
        click.echo()
        return

    if show_regression:
        target_dir = target or os.getcwd()
        regression_data = await store.get_regression(target_dir)
        if not regression_data:
            click.echo("\n  Not enough data for regression analysis (need 2+ battles).\n")
            return
        click.echo("\n  Regression Analysis\n  " + "=" * 40)
        new = regression_data["new_findings"]
        resolved = regression_data["resolved_findings"]
        click.echo(f"  New findings:      {len(new)}")
        click.echo(f"  Resolved findings: {len(resolved)}")
        for f in new[:5]:
            click.echo(f"    [NEW] {f.get('file_path', '?')}: {f.get('description', '?')[:60]}")
        for f in resolved[:5]:
            click.echo(f"    [RESOLVED] {f.get('file_path', '?')}: {f.get('description', '?')[:60]}")
        click.echo()
        return

    # Default: list recent battles
    query = BattleQuery(scenario=scenario, limit=limit)
    records = await store.query(query)

    if not records:
        click.echo("\n  No battle history found.\n")
        return

    click.echo(f"\n  Battle History ({len(records)} records)\n  " + "=" * 50)
    for r in records:
        click.echo(
            f"  {r.id}  {r.scenario.ljust(20)}  "
            f"{r.total_findings} findings  "
            f"{round(r.mitigation_coverage * 100)}% coverage  "
            f"{r.status}  {r.started_at[:10]}"
        )
    click.echo()


# --- Dashboard Command ---


@cli.command()
@click.option("-o", "--output", default=None, help="Output HTML file path")
@click.option("--target", default=None, help="Target directory for trends")
@click.option("--open-browser", is_flag=True, default=False, help="Open in browser after generating")
def dashboard(output: str | None, target: str | None, open_browser: bool) -> None:
    """Generate an HTML dashboard of battle history."""
    asyncio.run(_dashboard_async(output, target, open_browser))


async def _dashboard_async(output: str | None, target: str | None, open_browser: bool) -> None:
    from redteam_arena.core.battle_store import BattleStore
    from redteam_arena.server.dashboard import write_dashboard

    store = BattleStore()
    target_dir = target or os.getcwd()
    records = await store.query()
    trends = await store.get_trends(target_dir)

    path = await write_dashboard(records, trends, output_path=output or "")
    click.echo(f"\n  Dashboard generated: {path}\n")

    if open_browser:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(path)}")


if __name__ == "__main__":
    cli()
