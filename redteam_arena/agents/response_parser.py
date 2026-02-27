"""
Response parser -- extracts structured JSON blocks from agent output.
Agents stream natural language with embedded ```json blocks.
"""

from __future__ import annotations

import json
import re
import uuid

from redteam_arena.types import Confidence, Finding, Mitigation, Ok, Result, Severity

SEVERITY_VALUES = {"critical", "high", "medium", "low"}
CONFIDENCE_VALUES = {"high", "medium", "low"}


def _generate_id() -> str:
    """Generate a short unique ID (similar to nanoid(8))."""
    return uuid.uuid4().hex[:8]


def _extract_json_blocks(text: str) -> list[str]:
    """Extract all ```json ... ``` blocks from text."""
    blocks: list[str] = []
    for match in re.finditer(r"```json\s*\n([\s\S]*?)```", text):
        blocks.append(match.group(1).strip())
    return blocks


def _is_valid_severity(s: object) -> bool:
    return isinstance(s, str) and s.lower() in SEVERITY_VALUES


def _is_valid_confidence(c: object) -> bool:
    return isinstance(c, str) and c.lower() in CONFIDENCE_VALUES


def parse_findings(raw_output: str, round_number: int) -> Result[list[Finding], Exception]:
    """Parse findings from agent raw output."""
    json_blocks = _extract_json_blocks(raw_output)

    if not json_blocks:
        # Try to parse the entire output as JSON
        try:
            parsed = json.loads(raw_output)
            if isinstance(parsed, list):
                return _parse_findings_from_array(parsed, round_number)
        except (json.JSONDecodeError, ValueError):
            # No structured data found -- create a single finding from the text
            return Ok(
                value=[
                    Finding(
                        id=_generate_id(),
                        round_number=round_number,
                        file_path="unknown",
                        line_reference="0",
                        description=raw_output[:500],
                        attack_vector="See description",
                        severity="medium",
                    )
                ]
            )

    all_findings: list[Finding] = []

    for block in json_blocks:
        try:
            parsed = json.loads(block)
            items = parsed if isinstance(parsed, list) else [parsed]
            result = _parse_findings_from_array(items, round_number)
            if result.ok:
                all_findings.extend(result.value)
        except (json.JSONDecodeError, ValueError):
            continue

    return Ok(value=all_findings)


def _parse_findings_from_array(
    items: list[object], round_number: int
) -> Result[list[Finding], Exception]:
    """Parse a list of raw dicts into Finding objects."""
    findings: list[Finding] = []

    for item in items:
        if not isinstance(item, dict):
            continue

        obj: dict = item
        severity_raw = obj.get("severity", "medium")
        severity: Severity = severity_raw if _is_valid_severity(severity_raw) else "medium"

        code_snippet_raw = obj.get("codeSnippet") or obj.get("code_snippet")
        code_snippet = str(code_snippet_raw) if code_snippet_raw is not None else None

        findings.append(
            Finding(
                id=_generate_id(),
                round_number=round_number,
                file_path=str(
                    obj.get("filePath") or obj.get("file_path") or obj.get("file") or "unknown"
                ),
                line_reference=str(
                    obj.get("lineReference")
                    or obj.get("line_reference")
                    or obj.get("line")
                    or "0"
                ),
                description=str(
                    obj.get("description") or obj.get("desc") or "No description"
                ),
                attack_vector=str(
                    obj.get("attackVector")
                    or obj.get("attack_vector")
                    or obj.get("attack")
                    or "Not specified"
                ),
                severity=severity,
                code_snippet=code_snippet,
            )
        )

    return Ok(value=findings)


def parse_mitigations(
    raw_output: str,
    round_number: int,
    finding_ids: list[str],
) -> Result[list[Mitigation], Exception]:
    """Parse mitigations from agent raw output."""
    json_blocks = _extract_json_blocks(raw_output)

    if not json_blocks:
        # Create mitigations from raw text, one per finding
        return Ok(
            value=[
                Mitigation(
                    id=_generate_id(),
                    finding_id=finding_id,
                    round_number=round_number,
                    acknowledgment="Acknowledged",
                    proposed_fix=raw_output[:500],
                    confidence="medium",
                )
                for finding_id in finding_ids
            ]
        )

    all_mitigations: list[Mitigation] = []

    for block in json_blocks:
        try:
            parsed = json.loads(block)
            items = parsed if isinstance(parsed, list) else [parsed]

            for i, raw_item in enumerate(items):
                if not isinstance(raw_item, dict):
                    continue
                obj: dict = raw_item

                matching_finding_id = (
                    str(obj.get("findingId") or obj.get("finding_id") or "")
                    or (finding_ids[i] if i < len(finding_ids) else "")
                    or (finding_ids[0] if finding_ids else "")
                    or "unknown"
                )

                confidence_raw = obj.get("confidence", "medium")
                confidence: Confidence = (
                    confidence_raw if _is_valid_confidence(confidence_raw) else "medium"
                )

                all_mitigations.append(
                    Mitigation(
                        id=_generate_id(),
                        finding_id=matching_finding_id,
                        round_number=round_number,
                        acknowledgment=str(
                            obj.get("acknowledgment")
                            or obj.get("assessment")
                            or "Acknowledged"
                        ),
                        proposed_fix=str(
                            obj.get("proposedFix")
                            or obj.get("proposed_fix")
                            or obj.get("fix")
                            or obj.get("mitigation")
                            or "See response"
                        ),
                        confidence=confidence,
                    )
                )
        except (json.JSONDecodeError, ValueError):
            continue

    # If we parsed some but not enough for all findings, fill gaps
    if len(all_mitigations) < len(finding_ids):
        for i in range(len(all_mitigations), len(finding_ids)):
            all_mitigations.append(
                Mitigation(
                    id=_generate_id(),
                    finding_id=finding_ids[i],
                    round_number=round_number,
                    acknowledgment="Acknowledged",
                    proposed_fix="See battle log for details",
                    confidence="medium",
                )
            )

    return Ok(value=all_mitigations)
