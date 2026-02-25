"""Tests for redteam_arena.reports.battle_report."""

from __future__ import annotations

import re
from datetime import datetime

import pytest

from redteam_arena.reports.battle_report import generate_report
from redteam_arena.types import (
    Battle,
    BattleConfig,
    Finding,
    Mitigation,
    Round,
    Scenario,
)


# --- Helpers ---


def make_finding(**overrides: object) -> Finding:
    defaults = dict(
        id="find-001",
        round_number=1,
        file_path="src/db/queries.ts",
        line_reference="42",
        description="SQL injection via string concatenation in user query",
        attack_vector="Unsanitized user input passed directly into SQL string",
        severity="high",
        code_snippet=None,
    )
    defaults.update(overrides)
    return Finding(**defaults)  # type: ignore[arg-type]


def make_mitigation(**overrides: object) -> Mitigation:
    defaults = dict(
        id="mit-001",
        finding_id="find-001",
        round_number=1,
        acknowledgment="Confirmed SQL injection vulnerability",
        proposed_fix="Replace string concatenation with parameterized queries",
        confidence="high",
    )
    defaults.update(overrides)
    return Mitigation(**defaults)  # type: ignore[arg-type]


def make_round(
    number: int,
    findings: list[Finding],
    mitigations: list[Mitigation],
) -> Round:
    return Round(
        number=number,
        findings=findings,
        mitigations=mitigations,
        red_raw_output=f"Round {number} red agent output",
        blue_raw_output=f"Round {number} blue agent output",
    )


def make_battle(rounds: list[Round]) -> Battle:
    return Battle(
        id="battle-abc-123",
        config=BattleConfig(
            target_dir="/home/user/project",
            scenario=Scenario(
                name="sql-injection",
                description="Find SQL injection vectors",
                focus_areas=["Raw SQL", "User input"],
                severity_guidance="Critical for direct injection",
                red_guidance="Look for string concatenation",
                blue_guidance="Use parameterized queries",
                is_meta=False,
                sub_scenarios=[],
            ),
            rounds=len(rounds),
        ),
        rounds=rounds,
        events=[],
        status="completed",
        started_at=datetime(2024, 1, 15, 10, 0, 0),
        ended_at=datetime(2024, 1, 15, 10, 5, 0),
    )


# --- Tests ---


class TestBattleId:
    def test_includes_battle_id(self) -> None:
        battle = make_battle([make_round(1, [], [])])
        report = generate_report(battle)
        assert "battle-abc-123" in report

    def test_places_battle_id_in_header_table(self) -> None:
        battle = make_battle([make_round(1, [], [])])
        report = generate_report(battle)
        assert re.search(r"\*\*Battle ID\*\*.*battle-abc-123", report)


class TestSeverityCounts:
    def test_shows_severity_counts_in_summary_table(self) -> None:
        findings = [
            make_finding(id="f1", severity="critical"),
            make_finding(id="f2", severity="high"),
            make_finding(id="f3", severity="high"),
            make_finding(id="f4", severity="medium"),
            make_finding(id="f5", severity="low"),
        ]
        rnd = make_round(1, findings, [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "| Critical | 1 |" in report
        assert "| High | 2 |" in report
        assert "| Medium | 1 |" in report
        assert "| Low | 1 |" in report

    def test_shows_zero_counts_for_missing_severities(self) -> None:
        findings = [make_finding(id="f1", severity="critical")]
        rnd = make_round(1, findings, [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "| Critical | 1 |" in report
        assert "| High | 0 |" in report
        assert "| Medium | 0 |" in report
        assert "| Low | 0 |" in report

    def test_shows_total_finding_count_across_rounds(self) -> None:
        round1 = make_round(1, [make_finding(id="f1")], [])
        round2 = make_round(
            2,
            [make_finding(id="f2"), make_finding(id="f3")],
            [],
        )
        battle = make_battle([round1, round2])

        report = generate_report(battle)

        assert "**Total** | **3**" in report


class TestFindingDescriptions:
    def test_includes_finding_description(self) -> None:
        finding = make_finding(description="Critical SQL injection in login endpoint")
        rnd = make_round(1, [finding], [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "Critical SQL injection in login endpoint" in report

    def test_includes_file_path_and_line_reference(self) -> None:
        finding = make_finding(file_path="src/auth/login.ts", line_reference="87")
        rnd = make_round(1, [finding], [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "src/auth/login.ts:87" in report

    def test_includes_attack_vector(self) -> None:
        finding = make_finding(
            attack_vector="User-controlled username passed to raw query"
        )
        rnd = make_round(1, [finding], [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "User-controlled username passed to raw query" in report

    def test_includes_optional_code_snippet(self) -> None:
        finding = make_finding(
            code_snippet='db.query("SELECT * FROM users WHERE id=" + userId)',
        )
        rnd = make_round(1, [finding], [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert 'db.query("SELECT * FROM users WHERE id=" + userId)' in report


class TestMitigationDetails:
    def test_includes_proposed_fix(self) -> None:
        finding = make_finding(id="find-001")
        mitigation = make_mitigation(
            finding_id="find-001",
            proposed_fix="Use db.query('SELECT * FROM users WHERE id = ?', [userId])",
        )
        rnd = make_round(1, [finding], [mitigation])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "Use db.query('SELECT * FROM users WHERE id = ?', [userId])" in report

    def test_includes_acknowledgment(self) -> None:
        finding = make_finding(id="find-001")
        mitigation = make_mitigation(
            finding_id="find-001",
            acknowledgment="This is a confirmed high-severity SQL injection flaw",
        )
        rnd = make_round(1, [finding], [mitigation])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "This is a confirmed high-severity SQL injection flaw" in report

    def test_includes_confidence(self) -> None:
        finding = make_finding(id="find-001")
        mitigation = make_mitigation(finding_id="find-001", confidence="high")
        rnd = make_round(1, [finding], [mitigation])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert re.search(r"Confidence.*HIGH", report, re.IGNORECASE)

    def test_shows_mitigation_coverage_percentage(self) -> None:
        f1 = make_finding(id="f1")
        f2 = make_finding(id="f2")
        m1 = make_mitigation(finding_id="f1")
        rnd = make_round(1, [f1, f2], [m1])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "1/2" in report
        assert "50%" in report


class TestZeroFindings:
    def test_shows_no_vulnerabilities_found(self) -> None:
        rnd = make_round(1, [], [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "No vulnerabilities found." in report

    def test_does_not_include_finding_detail_section(self) -> None:
        rnd = make_round(1, [], [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert not re.search(r"Finding \d+:", report)

    def test_shows_100_percent_mitigation_coverage(self) -> None:
        rnd = make_round(1, [], [])
        battle = make_battle([rnd])

        report = generate_report(battle)

        assert "0/0" in report
        assert "100%" in report


class TestGeneralReportStructure:
    def test_includes_header(self) -> None:
        battle = make_battle([make_round(1, [], [])])
        report = generate_report(battle)
        assert "# RedTeam Arena Battle Report" in report

    def test_includes_scenario_name(self) -> None:
        battle = make_battle([make_round(1, [], [])])
        report = generate_report(battle)
        assert "sql-injection" in report

    def test_includes_battle_log_section(self) -> None:
        battle = make_battle([make_round(1, [], [])])
        report = generate_report(battle)
        assert "## Battle Log" in report

    def test_returns_non_empty_string(self) -> None:
        battle = make_battle([make_round(1, [], [])])
        report = generate_report(battle)
        assert isinstance(report, str)
        assert len(report) > 0
