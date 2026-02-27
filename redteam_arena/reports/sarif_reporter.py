"""
SARIF 2.1.0 reporter — generates Static Analysis Results Interchange Format.
Compatible with GitHub Security tab and VS Code SARIF viewers.
Also generates structured JSON reports.
"""

from __future__ import annotations

import hashlib
import json
import re

from redteam_arena.types import Battle, Finding

SEVERITY_TO_LEVEL: dict[str, str] = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "note",
}

SEVERITY_TO_CVSS: dict[str, str] = {
    "critical": "9.0",
    "high": "7.5",
    "medium": "5.0",
    "low": "2.0",
}


def generate_sarif_report(battle: Battle) -> str:
    """Generate a SARIF 2.1.0 JSON report."""
    all_findings = [f for r in battle.rounds for f in r.findings]
    all_mitigations = [m for r in battle.rounds for m in r.mitigations]

    rules: list[dict] = []
    results: list[dict] = []
    rule_map: dict[str, int] = {}

    for finding in all_findings:
        rule_id = _build_rule_id(finding, battle.config.scenario.name)

        if rule_id in rule_map:
            rule_index = rule_map[rule_id]
        else:
            rule_index = len(rules)
            rule_map[rule_id] = rule_index

            mitigation = next(
                (m for m in all_mitigations if m.finding_id == finding.id), None
            )

            rules.append({
                "id": rule_id,
                "name": rule_id,
                "shortDescription": {
                    "text": _truncate(finding.description, 1024),
                },
                "fullDescription": {
                    "text": _truncate(
                        f"{finding.description}\n\nAttack vector: {finding.attack_vector}",
                        1024,
                    ),
                },
                "defaultConfiguration": {
                    "level": SEVERITY_TO_LEVEL[finding.severity],
                },
                "help": {
                    "text": (
                        f"Mitigation: {mitigation.proposed_fix}"
                        if mitigation
                        else "No mitigation proposed."
                    ),
                    "markdown": (
                        f"**Mitigation** ({mitigation.confidence} confidence):\n\n{mitigation.proposed_fix}"
                        if mitigation
                        else "*No mitigation proposed.*"
                    ),
                },
                "properties": {
                    "tags": ["security", battle.config.scenario.name],
                    "precision": "medium",
                    "problem.severity": SEVERITY_TO_LEVEL[finding.severity],
                    "security-severity": SEVERITY_TO_CVSS[finding.severity],
                },
            })

        line_number = _parse_line_number(finding.line_reference)

        results.append({
            "ruleId": rule_id,
            "ruleIndex": rule_index,
            "level": SEVERITY_TO_LEVEL[finding.severity],
            "message": {
                "text": f"{finding.description}\n\nAttack vector: {finding.attack_vector}",
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": _normalize_file_path(finding.file_path),
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": line_number,
                            "startColumn": 1,
                        },
                    },
                },
            ],
            "partialFingerprints": {
                "primaryLocationLineHash": _hash_fingerprint(
                    finding.file_path,
                    finding.line_reference,
                    finding.description,
                ),
            },
        })

    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "redteam-arena",
                        "semanticVersion": "0.1.0",
                        "informationUri": "https://github.com/DilawarShafiq/redteam-arena",
                        "rules": rules,
                    },
                },
                "results": results,
                "columnKind": "utf16CodeUnits",
            },
        ],
    }

    return json.dumps(sarif, indent=2)


def generate_json_report(battle: Battle) -> str:
    """Generate a structured JSON report."""
    all_findings = [f for r in battle.rounds for f in r.findings]
    all_mitigations = [m for r in battle.rounds for m in r.mitigations]

    by_severity: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        by_severity[f.severity] += 1

    report = {
        "battleId": battle.id,
        "scenario": battle.config.scenario.name,
        "targetDir": battle.config.target_dir,
        "status": battle.status,
        "startedAt": battle.started_at.isoformat(),
        "endedAt": battle.ended_at.isoformat() if battle.ended_at else None,
        "summary": {
            "totalRounds": len(battle.rounds),
            "totalFindings": len(all_findings),
            "findingsBySeverity": by_severity,
            "totalMitigations": len(all_mitigations),
            "mitigationCoverage": (
                round((len(all_mitigations) / len(all_findings)) * 100)
                if all_findings
                else 100
            ),
        },
        "rounds": [
            {
                "number": r.number,
                "findings": [
                    {
                        "id": f.id,
                        "severity": f.severity,
                        "filePath": f.file_path,
                        "lineReference": f.line_reference,
                        "description": f.description,
                        "attackVector": f.attack_vector,
                        "codeSnippet": f.code_snippet,
                    }
                    for f in r.findings
                ],
                "mitigations": [
                    {
                        "id": m.id,
                        "findingId": m.finding_id,
                        "confidence": m.confidence,
                        "acknowledgment": m.acknowledgment,
                        "proposedFix": m.proposed_fix,
                    }
                    for m in r.mitigations
                ],
            }
            for r in battle.rounds
        ],
    }

    return json.dumps(report, indent=2)


def _build_rule_id(finding: Finding, scenario: str) -> str:
    prefix = "RT"
    slug = scenario.replace("-", "")[:4].upper()
    hash_val = hashlib.md5(
        finding.description[:50].encode()
    ).hexdigest()[:4].upper()
    return f"{prefix}-{slug}-{hash_val}"


def _parse_line_number(line_ref: str) -> int:
    match = re.search(r"(\d+)", line_ref)
    return int(match.group(1)) if match else 1


def _normalize_file_path(file_path: str) -> str:
    return file_path.replace("\\", "/")


def _hash_fingerprint(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
