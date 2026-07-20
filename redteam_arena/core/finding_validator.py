"""
Finding validation -- checks model-reported locations against the real files.

Findings arrive as free-form model output: a path, a line reference and
sometimes a quoted snippet, none of which is guaranteed to correspond to
anything. Left unchecked, a hallucinated location is indistinguishable from a
real one in every report, in SARIF output and in `--fail-on` gating.

This module re-reads nothing. The file contents the agents were shown are
already in memory, so validation is a cheap string check against the exact
bytes the model saw.
"""

from __future__ import annotations

import re

from redteam_arena.types import FileEntry, Finding

# Model line references are free text: "42", "L42", "lines 42-58", "42 (approx)".
_LINE_PATTERN = re.compile(r"\d+")

# Snippets get reformatted by the model even when the finding is real, so
# compare on non-whitespace content rather than demanding a literal match.
_WHITESPACE = re.compile(r"\s+")


def validate_findings(findings: list[Finding], files: list[FileEntry]) -> list[Finding]:
    """Annotate each finding with whether its reported location holds up.

    Returns the same Finding objects, mutated in place, so callers keep their
    existing references. Findings are never dropped -- an unverified finding may
    still be a real issue the model mislocated, and silently discarding it would
    trade one failure mode for another.
    """
    by_path = {f.path: f for f in files}
    # Models frequently return a path relative to a different root, so fall back
    # to a unique basename match before giving up.
    by_basename: dict[str, list[FileEntry]] = {}
    for scanned in files:
        by_basename.setdefault(_basename(scanned.path), []).append(scanned)

    for finding in findings:
        entry: FileEntry | None = _resolve_file(finding.file_path, by_path, by_basename)
        if entry is None:
            finding.verification = "not_in_scope"
            finding.verification_detail = (
                f"No file matching '{finding.file_path}' was read during this scan."
            )
            continue

        problems = _check_location(finding, entry)
        if problems:
            finding.verification = "unverified"
            finding.verification_detail = " ".join(problems)
        else:
            finding.verification = "verified"
            finding.verification_detail = f"Location confirmed in '{entry.path}'."

    return findings


def _resolve_file(
    reported_path: str,
    by_path: dict[str, FileEntry],
    by_basename: dict[str, list[FileEntry]],
) -> FileEntry | None:
    """Match a model-reported path to a file that was actually read."""
    if not reported_path or reported_path == "unknown":
        return None

    normalized = reported_path.replace("\\", "/").lstrip("./")
    for candidate_path, entry in by_path.items():
        if candidate_path.replace("\\", "/") == normalized:
            return entry

    # Unique basename match only. If two files share a name we cannot tell which
    # was meant, and guessing would manufacture false confidence.
    matches = by_basename.get(_basename(normalized), [])
    if len(matches) == 1:
        return matches[0]
    return None


def _check_location(finding: Finding, entry: FileEntry) -> list[str]:
    """Return a list of problems with the finding's location; empty means good."""
    problems: list[str] = []
    lines = entry.content.splitlines()

    line_no = _parse_line(finding.line_reference)
    if line_no is None:
        problems.append(f"Line reference '{finding.line_reference}' is not a usable line number.")
    elif line_no < 1 or line_no > len(lines):
        problems.append(
            f"Line {line_no} is outside '{entry.path}', which has {len(lines)} lines."
        )

    if finding.code_snippet:
        if not _snippet_present(finding.code_snippet, entry.content):
            problems.append("The quoted snippet does not appear in the file.")

    return problems


def _parse_line(line_reference: str) -> int | None:
    """Pull the first integer out of a free-form line reference."""
    match = _LINE_PATTERN.search(line_reference or "")
    return int(match.group()) if match else None


def _snippet_present(snippet: str, content: str) -> bool:
    """Whitespace-insensitive containment check.

    Compares the snippet's first non-empty line rather than the whole block:
    models routinely elide the middle of a quote with an ellipsis, and requiring
    the full block would fail findings that are otherwise sound.
    """
    normalized_content = _WHITESPACE.sub(" ", content)
    for raw_line in snippet.splitlines():
        candidate = _WHITESPACE.sub(" ", raw_line).strip()
        if len(candidate) < 8:  # too short to be evidence of anything
            continue
        return candidate in normalized_content
    return False


def _basename(path: str) -> str:
    return path.replace("\\", "/").rsplit("/", 1)[-1]


def verification_counts(findings: list[Finding]) -> dict[str, int]:
    """Tally findings by verification status, for report summaries."""
    counts = {"verified": 0, "unverified": 0, "not_in_scope": 0, "unchecked": 0}
    for finding in findings:
        counts[finding.verification] = counts.get(finding.verification, 0) + 1
    return counts
