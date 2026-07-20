"""Tests for redteam_arena.reports.compliance_reporter.

These focus on what the document *claims*. The report is unverified LLM output
about regulated frameworks, so overclaiming is the primary defect to guard
against -- see the disclaimer requirements below.
"""

from __future__ import annotations

from datetime import datetime

from redteam_arena.reports.compliance_reporter import generate_compliance_report
from redteam_arena.types import (
    Battle,
    BattleConfig,
    Finding,
    Mitigation,
    Round,
    ScanScope,
    Scenario,
)


def make_finding(**overrides: object) -> Finding:
    defaults = dict(
        id="find-001",
        round_number=1,
        file_path="src/auth/session.py",
        line_reference="88",
        description="Session tokens are not rotated after privilege change",
        attack_vector="Session fixation enables privilege retention",
        severity="high",
        code_snippet=None,
    )
    defaults.update(overrides)
    return Finding(**defaults)  # type: ignore[arg-type]


def make_battle(
    findings: list[Finding],
    mitigations: list[Mitigation] | None = None,
    scope: ScanScope | None = None,
) -> Battle:
    return Battle(
        id="battle-compliance-1",
        config=BattleConfig(
            target_dir="/home/user/project",
            scenario=Scenario(
                name="soc2-security-privacy",
                description="SOC 2 control gap review",
                focus_areas=["Access control"],
                severity_guidance="Critical for missing MFA",
                red_guidance="Check control coverage",
                blue_guidance="Propose remediations",
                is_meta=False,
                sub_scenarios=[],
            ),
            rounds=1,
        ),
        rounds=[
            Round(
                number=1,
                findings=findings,
                mitigations=mitigations or [],
                red_raw_output="",
                blue_raw_output="",
            )
        ],
        events=[],
        status="completed",
        started_at=datetime(2026, 7, 21, 9, 0, 0),
        ended_at=datetime(2026, 7, 21, 9, 5, 0),
        scan_scope=scope,
    )


class TestNoOverclaiming:
    """The report must never present itself as an audit or certification."""

    def test_does_not_claim_to_be_an_audit(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        lowered = report.lower()
        assert "compliance audit report" not in lowered
        assert "independent cybersecurity" not in lowered

    def test_states_it_is_not_an_audit(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        assert "not an audit, certification, or independent assessment" in report.lower()

    def test_names_the_third_party_requirement(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        lowered = report.lower()
        assert "independent, accredited third party" in lowered
        assert "no software can" in lowered

    def test_marks_output_as_unverified(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        assert "unverified" in report.lower()

    def test_does_not_present_slas_as_binding(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        assert "Remediation SLA" not in report
        assert "Suggested triage priority" in report

    def test_disclaimer_appears_at_top_and_bottom(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        assert report.lower().count("not an audit, certification") >= 2


class TestEmptyResults:
    """An empty run is inconclusive, never a pass."""

    def test_empty_findings_do_not_read_as_compliant(self) -> None:
        report = generate_compliance_report(make_battle([]))
        lowered = report.lower()
        assert "no significant control gaps" not in lowered
        assert "inconclusive run, not a passing one" in lowered

    def test_empty_findings_warn_about_partial_review(self) -> None:
        report = generate_compliance_report(make_battle([]))
        assert "not** evidence that the" in report


class TestScopeDisclosure:
    def test_partial_scope_is_disclosed(self) -> None:
        scope = ScanScope(
            files_read=2,
            bytes_read=102400,
            max_total_size=102400,
            budget_exhausted=True,
        )
        report = generate_compliance_report(make_battle([make_finding()], scope=scope))
        assert "Scan Scope" in report
        assert "partial" in report.lower()

    def test_missing_scope_does_not_break_report(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()], scope=None))
        assert "Control Gap Analysis" in report


class TestFindingsRendering:
    def test_locations_carry_a_verification_result(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        assert "**Location check:**" in report
        # Findings built without a validation pass must not read as confirmed.
        assert "Not validated" in report

    def test_renders_finding_content(self) -> None:
        report = generate_compliance_report(make_battle([make_finding()]))
        assert "Session tokens are not rotated" in report
        assert "src/auth/session.py:88" in report
