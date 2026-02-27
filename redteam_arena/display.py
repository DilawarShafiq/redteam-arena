"""
Terminal display -- rich-based formatters for battle output.
Handles real-time streaming display and summary formatting.
"""

from rich.console import Console
from rich.text import Text

from redteam_arena.types import (
    BattleSummary,
    Finding,
    Mitigation,
)

console = Console()
_err_console = Console(stderr=True)

SEVERITY_STYLES: dict[str, str] = {
    "critical": "bold white on red",
    "high": "bold red",
    "medium": "yellow",
    "low": "dim",
}

SEVERITY_LABELS: dict[str, str] = {
    "critical": "CRITICAL",
    "high": "HIGH",
    "medium": "MEDIUM",
    "low": "LOW",
}


def display_battle_header(scenario: str, target_dir: str) -> None:
    console.print()
    console.print("  REDTEAM ARENA v0.0.1", style="bold white")
    console.print(f"  Scenario: {scenario} | Target: {target_dir}", style="dim")
    console.print("  " + "=" * 50, style="dim")
    console.print()


def display_round_start(round_number: int, total_rounds: int) -> None:
    console.print(f"\n  Round {round_number}/{total_rounds}", style="bold white")
    console.print("  " + "-" * 40, style="dim")


def display_red_chunk(chunk: str) -> None:
    console.print(chunk, style="red", end="")


def display_blue_chunk(chunk: str) -> None:
    console.print(chunk, style="blue", end="")


def display_red_header() -> None:
    console.print()
    console.print("  RED AGENT (Attacker):", style="bold red")
    console.print()
    console.print("  ", end="")


def display_blue_header() -> None:
    console.print()
    console.print("  BLUE AGENT (Defender):", style="bold blue")
    console.print()
    console.print("  ", end="")


def display_agent_done() -> None:
    console.print()


def display_finding(finding: Finding) -> None:
    severity_label = SEVERITY_LABELS.get(finding.severity, "UNKNOWN")
    severity_style = SEVERITY_STYLES.get(finding.severity, "dim")

    badge = Text(f" {severity_label} ", style=severity_style)
    console.print(Text("  "), badge, Text(f" {finding.file_path}:{finding.line_reference}", style="red"))
    console.print(f"    {finding.description}", style="red")
    if finding.attack_vector:
        console.print(f"    Attack: {finding.attack_vector}", style="dim red")


def display_mitigation(mitigation: Mitigation) -> None:
    if mitigation.confidence == "high":
        conf_badge = "[green][HIGH][/green]"
    elif mitigation.confidence == "medium":
        conf_badge = "[yellow][MED][/yellow]"
    else:
        conf_badge = "[dim][LOW][/dim]"

    console.print(f"  {conf_badge} {mitigation.acknowledgment}", style="blue")
    console.print(f"    Fix: {mitigation.proposed_fix}", style="blue")


def display_round_end(
    round_number: int,
    finding_count: int,
    mitigation_count: int,
) -> None:
    console.print(
        f"\n  Round {round_number}: {finding_count} finding(s), {mitigation_count} mitigation(s)",
        style="dim",
    )


def display_battle_summary(summary: BattleSummary) -> None:
    console.print()
    console.print("  " + "=" * 50, style="bold white")
    console.print("  Battle Report Summary", style="bold white")
    console.print("  " + "=" * 50, style="bold white")
    console.print()
    console.print(
        f"  Rounds: {summary.total_rounds}  |  Vulnerabilities: {summary.total_findings}",
        style="white",
    )

    fbs = summary.findings_by_severity
    parts: list[str] = []
    if fbs.get("critical", 0) > 0:
        parts.append(f"[bold white on red] Critical: {fbs['critical']} [/bold white on red]")
    if fbs.get("high", 0) > 0:
        parts.append(f"[bold red]High: {fbs['high']}[/bold red]")
    if fbs.get("medium", 0) > 0:
        parts.append(f"[yellow]Medium: {fbs['medium']}[/yellow]")
    if fbs.get("low", 0) > 0:
        parts.append(f"[dim]Low: {fbs['low']}[/dim]")

    if parts:
        severity_line = "  |  ".join(parts)
        console.print(f"  {severity_line}")

    coverage = round(summary.mitigation_coverage * 100)
    console.print(
        f"  Mitigations proposed: {summary.total_mitigations}/{summary.total_findings} ({coverage}%)",
        style="blue",
    )


def display_report_path(path: str) -> None:
    console.print()
    console.print(f"  Full report: {path}", style="bold green")
    console.print()


def display_error(message: str) -> None:
    _err_console.print(f"\n  Error: {message}\n", style="bold red")


def display_warning(message: str) -> None:
    console.print(f"  Warning: {message}", style="yellow")


def display_no_findings() -> None:
    console.print()
    console.print("  No vulnerabilities found!", style="bold green")
    console.print("  The codebase looks clean for this scenario.", style="green")
    console.print()


def display_interrupted() -> None:
    console.print()
    console.print("  Battle interrupted.", style="bold yellow")
