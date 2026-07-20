"""
Compliance Reporter -- high-end compliance and security audit reporting.
Generates an Executive Summary and Detailed Technical Report in Markdown.
"""

from __future__ import annotations

import os

from redteam_arena.reports.scope_notice import format_scan_scope
from redteam_arena.types import Battle, Finding, Mitigation

_DISCLAIMER = """> ⚠️ **This is not an audit, certification, or independent assessment.**
>
> This document is unverified output from a large language model that read a
> subset of the target's source code. Findings may be incomplete, inaccurate, or
> hallucinated, and the absence of a finding does not indicate the absence of a
> control gap.
>
> SOC 2, ISO 27001, HITRUST, PCI DSS, FedRAMP and comparable programs require an
> examination by an independent, accredited third party — a licensed CPA firm, an
> accredited certification body, or an approved external assessor. No software can
> produce, replace, or substitute for that engagement. Use this document only as
> preparatory input for qualified human reviewers."""


def generate_compliance_report(battle: Battle) -> str:
    """Generate a high-end compliance and security audit report."""
    all_findings: list[Finding] = []
    all_mitigations: list[Mitigation] = []
    for r in battle.rounds:
        all_findings.extend(r.findings)
        all_mitigations.extend(r.mitigations)

    lines: list[str] = []

    # Title Page
    lines.append("# Control Gap Analysis")
    lines.append("## Automated Pre-Audit Input — Unverified")
    lines.append("")
    lines.append(f"**Date:** {battle.started_at.strftime('%B %d, %Y')}")
    lines.append(f"**Target Application:** `{battle.config.target_dir}`")
    lines.append(f"**Reference Framework/Scenario:** {battle.config.scenario.name}")
    lines.append(f"**Run ID:** {battle.id}")
    lines.append("")
    lines.append(_DISCLAIMER)
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## 1. Summary")
    lines.append("")
    lines.append("This document lists potential control gaps suggested by an automated language-model "
                 "review of source code. It is a starting point for human analysis, not an assessment "
                 "of the target environment's security, privacy, or processing integrity.")
    lines.append("")

    total = len(all_findings)
    lines.append(f"**Potential control gaps suggested:** {total}")
    lines.append("")
    lines.extend(format_scan_scope(battle.scan_scope))

    by_severity: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        by_severity[f.severity] += 1

    lines.append("### Suggested Severity Breakdown")
    lines.append("")
    lines.append("Severities are model-assigned and unvalidated. Triage priorities are a")
    lines.append("common default, not a contractual or regulatory SLA.")
    lines.append("")
    lines.append("| Model-assigned severity | Count | Suggested triage priority |")
    lines.append("|-------------------------|-------|---------------------------|")
    lines.append(f"| **Critical** | {by_severity['critical']} | Triage first |")
    lines.append(f"| **High** | {by_severity['high']} | Triage within days |")
    lines.append(f"| **Medium** | {by_severity['medium']} | Scheduled review |")
    lines.append(f"| **Low** | {by_severity['low']} | Backlog |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Detailed Findings
    lines.append("## 2. Suggested Control Gaps")
    lines.append("")

    if not all_findings:
        lines.append("*This run surfaced no candidate control gaps. This is **not** evidence that the "
                     "target is compliant or secure — the model may have reviewed only part of the "
                     "codebase, or missed gaps that are present. Treat an empty result as an "
                     "inconclusive run, not a passing one.*")
        lines.append("")
    else:
        for i, finding in enumerate(all_findings):
            mitigation = next(
                (m for m in all_mitigations if m.finding_id == finding.id), None
            )

            lines.append(f"### Candidate {i + 1}: {finding.description}")
            lines.append(f"**Model-assigned severity:** {finding.severity.upper()}")
            lines.append(f"**Reported location:** `{finding.file_path}:{finding.line_reference}` "
                         "(model-reported — confirm before relying on it)")
            lines.append(f"**Control Impact / Attack Vector:** {finding.attack_vector}")
            lines.append("")

            if finding.code_snippet:
                lines.append("**Model-quoted snippet (not verified against the file):**")
                lines.append("```")
                lines.append(finding.code_snippet)
                lines.append("```")
                lines.append("")
                
            if mitigation:
                lines.append("**Suggested remediation (model-generated, unreviewed):**")
                lines.append(f"> {mitigation.acknowledgment}")
                lines.append(f"**Proposed fix:** {mitigation.proposed_fix}")
                lines.append(f"**Model confidence:** {mitigation.confidence.upper()}")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Conclusion & Next Steps
    lines.append("## 3. Next Steps")
    lines.append("Have a qualified reviewer confirm each candidate above against the actual "
                 "codebase before acting on it, discarding those that do not reproduce. Surviving "
                 "items can then be tracked through your normal remediation process and, where "
                 "relevant, provided as preparatory input to your auditor or assessor.")
    lines.append("")
    lines.append(_DISCLAIMER)

    return "\n".join(lines)


async def write_compliance_report(
    content: str,
    battle_id: str,
    *,
    output_path: str = "",
) -> str:
    """Write the report to a file and return the file path."""
    if output_path:
        filepath = output_path
    else:
        filename = f"compliance-report-{battle_id}.md"
        filepath = os.path.join(os.getcwd(), filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath
