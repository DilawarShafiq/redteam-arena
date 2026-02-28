"""
Compliance Reporter -- high-end compliance and security audit reporting.
Generates an Executive Summary and Detailed Technical Report in Markdown.
"""

from __future__ import annotations

import os

from redteam_arena.types import Battle, Finding, Mitigation


def generate_compliance_report(battle: Battle) -> str:
    """Generate a high-end compliance and security audit report."""
    all_findings: list[Finding] = []
    all_mitigations: list[Mitigation] = []
    for r in battle.rounds:
        all_findings.extend(r.findings)
        all_mitigations.extend(r.mitigations)

    lines: list[str] = []

    # Title Page
    lines.append("# ENTERPRISE COMPLIANCE AUDIT REPORT")
    lines.append("## Independent Cybersecurity & Compliance Assessment")
    lines.append("")
    lines.append(f"**Date:** {battle.started_at.strftime('%B %d, %Y')}")
    lines.append(f"**Target Application:** `{battle.config.target_dir}`")
    lines.append(f"**Assessment Framework/Scenario:** {battle.config.scenario.name}")
    lines.append(f"**Report ID:** {battle.id}")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Executive Summary
    lines.append("## 1. Executive Summary")
    lines.append("")
    lines.append("This report outlines the results of a comprehensive cybersecurity and compliance assessment. "
                 "The assessment aimed to identify control gaps, architectural flaws, and vulnerabilities "
                 "that could impact the security, privacy, and processing integrity of the target environment.")
    lines.append("")
    
    total = len(all_findings)
    lines.append(f"**Total Control Failures/Vulnerabilities Identified:** {total}")
    lines.append("")

    by_severity: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        by_severity[f.severity] += 1

    lines.append("### Risk Posture Overview")
    lines.append("| Severity | Count | Remediation SLA |")
    lines.append("|----------|-------|-----------------|")
    lines.append(f"| **Critical** | {by_severity['critical']} | Immediate / 24 Hours |")
    lines.append(f"| **High** | {by_severity['high']} | 7 Days |")
    lines.append(f"| **Medium** | {by_severity['medium']} | 30 Days |")
    lines.append(f"| **Low** | {by_severity['low']} | 90 Days |")
    lines.append("")

    lines.append("---")
    lines.append("")

    # Detailed Findings
    lines.append("## 2. Detailed Technical Findings & Control Gaps")
    lines.append("")
    
    if not all_findings:
        lines.append("*No significant control gaps or vulnerabilities were identified during this assessment cycle.*")
        lines.append("")
    else:
        for i, finding in enumerate(all_findings):
            mitigation = next(
                (m for m in all_mitigations if m.finding_id == finding.id), None
            )

            lines.append(f"### Finding {i + 1}: {finding.description}")
            lines.append(f"**Severity:** {finding.severity.upper()}")
            lines.append(f"**Location:** `{finding.file_path}:{finding.line_reference}`")
            lines.append(f"**Control Impact / Attack Vector:** {finding.attack_vector}")
            lines.append("")
            
            if finding.code_snippet:
                lines.append("**Evidence / Code Snippet:**")
                lines.append("```")
                lines.append(finding.code_snippet)
                lines.append("```")
                lines.append("")
                
            if mitigation:
                lines.append("**Management Response / Proposed Remediation:**")
                lines.append(f"> {mitigation.acknowledgment}")
                lines.append(f"**Technical Fix:** {mitigation.proposed_fix}")
                lines.append(f"**Confidence Level:** {mitigation.confidence.upper()}")
                lines.append("")

            lines.append("---")
            lines.append("")

    # Conclusion & Next Steps
    lines.append("## 3. Conclusion & Next Steps")
    lines.append("Management is advised to review these findings and implement the proposed remediations "
                 "according to the recommended SLAs. Re-testing is recommended following the deployment of fixes.")
    lines.append("")
    lines.append("*(End of Report)*")

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
