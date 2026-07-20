"""
SARIF 2.1.0 reporter — generates Static Analysis Results Interchange Format.
Compatible with GitHub Security tab and VS Code SARIF viewers.
Also generates structured JSON reports.
"""

from __future__ import annotations

import hashlib
import json
import os
import re

from redteam_arena import __version__
from redteam_arena.types import Battle

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
    """Generate a SARIF 2.1.0 JSON report.

    Paths are emitted relative to the enclosing git repository root so GitHub
    code scanning can map results onto files in the commit; rule IDs and
    fingerprints are derived only from stable inputs so alerts persist across
    runs instead of being re-created every scan.
    """
    all_findings = [f for r in battle.rounds for f in r.findings]
    all_mitigations = [m for r in battle.rounds for m in r.mitigations]

    path_prefix = _repo_relative_prefix(battle.config.target_dir)

    rules: list[dict] = []
    results: list[dict] = []
    rule_map: dict[str, int] = {}

    for finding in all_findings:
        rule_id = _build_rule_id(battle.config.scenario.name)

        if rule_id in rule_map:
            rule_index = rule_map[rule_id]
        else:
            rule_index = len(rules)
            rule_map[rule_id] = rule_index

            mitigation = next(
                (m for m in all_mitigations if m.finding_id == finding.id), None
            )

            scenario_name = battle.config.scenario.name
            rules.append({
                "id": rule_id,
                "name": _rule_name(scenario_name),
                "shortDescription": {
                    "text": _truncate(
                        battle.config.scenario.description or scenario_name, 1024
                    ),
                },
                "fullDescription": {
                    "text": _truncate(
                        f"Findings from the '{scenario_name}' scenario. "
                        "Each result describes a specific reported issue.",
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
        uri = _repo_relative_uri(path_prefix, finding.file_path)

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
                            "uri": uri,
                        },
                        "region": {
                            "startLine": line_number,
                            "startColumn": 1,
                        },
                    },
                },
            ],
            # Location-based only. The description is LLM prose that differs
            # between runs; including it made every scan look like new alerts.
            "partialFingerprints": {
                "primaryLocationLineHash": _hash_fingerprint(
                    uri, rule_id, str(line_number)
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
                        "semanticVersion": __version__,
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


def _build_rule_id(scenario: str) -> str:
    """A stable rule id per scenario.

    A SARIF rule is a reusable category, not one finding. Deriving the id from
    the scenario alone keeps it identical across runs; the previous MD5 of the
    finding's prose changed whenever the model reworded itself, so GitHub saw a
    brand-new rule -- and brand-new alerts -- every scan.
    """
    return f"redteam-arena/{scenario}"


def _rule_name(scenario: str) -> str:
    """PascalCase rule name, e.g. sql-injection -> SqlInjection."""
    return "".join(part.capitalize() for part in re.split(r"[-_]", scenario) if part)


def _parse_line_number(line_ref: str) -> int:
    match = re.search(r"(\d+)", line_ref)
    return int(match.group(1)) if match else 1


def _normalize_file_path(file_path: str) -> str:
    return file_path.replace("\\", "/").lstrip("/")


def _repo_relative_prefix(target_dir: str) -> str:
    """Path from the enclosing git repo root down to the scanned directory.

    GitHub code scanning resolves result URIs against the repository root, but
    findings carry paths relative to the scanned directory. When the scan
    target sits inside a git repo, prepend the offset so `battle ./src` yields
    `src/...`. Pure filesystem walk -- no git subprocess. Empty string when the
    target is the repo root or not in a repo.
    """
    try:
        current = os.path.abspath(target_dir)
    except (OSError, ValueError):
        return ""
    walked = current
    while True:
        if os.path.isdir(os.path.join(walked, ".git")):
            rel = os.path.relpath(current, walked)
            return "" if rel == "." else _normalize_file_path(rel)
        parent = os.path.dirname(walked)
        if parent == walked:  # reached filesystem root
            return ""
        walked = parent


def _repo_relative_uri(prefix: str, file_path: str) -> str:
    """Join the repo-root prefix with a finding's path, as a POSIX URI."""
    normalized = _normalize_file_path(file_path)
    if prefix:
        return f"{prefix}/{normalized}"
    return normalized


def _hash_fingerprint(*parts: str) -> str:
    return hashlib.sha256(":".join(parts).encode()).hexdigest()[:16]


def _truncate(text: str, max_len: int) -> str:
    return text if len(text) <= max_len else text[: max_len - 3] + "..."
