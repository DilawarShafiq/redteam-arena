"""Tests for redteam_arena.core.finding_validator.

The point of validation is to separate findings that name a real location from
those that do not, so the hallucination cases matter as much as the happy path.
"""

from __future__ import annotations

from redteam_arena.core.finding_validator import validate_findings, verification_counts
from redteam_arena.types import FileEntry, Finding

SAMPLE = """def login(user, password):
    query = "SELECT * FROM users WHERE name = '" + user + "'"
    cursor.execute(query)
    return cursor.fetchone()
"""


def make_finding(**overrides: object) -> Finding:
    defaults = dict(
        id="find-001",
        round_number=1,
        file_path="app/auth.py",
        line_reference="2",
        description="SQL injection via string concatenation",
        attack_vector="Unsanitized user input concatenated into SQL",
        severity="high",
        code_snippet=None,
    )
    defaults.update(overrides)
    return Finding(**defaults)  # type: ignore[arg-type]


def files() -> list[FileEntry]:
    return [FileEntry(path="app/auth.py", content=SAMPLE)]


class TestVerifiedFindings:
    def test_valid_path_and_line_verifies(self) -> None:
        finding = make_finding()

        validate_findings([finding], files())

        assert finding.verification == "verified"

    def test_matching_snippet_verifies(self) -> None:
        finding = make_finding(code_snippet='    cursor.execute(query)')

        validate_findings([finding], files())

        assert finding.verification == "verified"

    def test_snippet_match_ignores_whitespace(self) -> None:
        finding = make_finding(code_snippet="cursor.execute(query)")

        validate_findings([finding], files())

        assert finding.verification == "verified"

    def test_messy_line_reference_still_parses(self) -> None:
        finding = make_finding(line_reference="lines 2-3")

        validate_findings([finding], files())

        assert finding.verification == "verified"


class TestHallucinatedLocations:
    def test_unknown_file_is_not_in_scope(self) -> None:
        finding = make_finding(file_path="src/does/not/exist.py")

        validate_findings([finding], files())

        assert finding.verification == "not_in_scope"
        assert "was read" in finding.verification_detail

    def test_line_past_end_of_file_is_unverified(self) -> None:
        finding = make_finding(line_reference="9999")

        validate_findings([finding], files())

        assert finding.verification == "unverified"
        assert "outside" in finding.verification_detail

    def test_absent_snippet_is_unverified(self) -> None:
        finding = make_finding(code_snippet="os.system(user_input)  # not in the file")

        validate_findings([finding], files())

        assert finding.verification == "unverified"
        assert "snippet" in finding.verification_detail

    def test_unparseable_line_reference_is_unverified(self) -> None:
        finding = make_finding(line_reference="somewhere near the top")

        validate_findings([finding], files())

        assert finding.verification == "unverified"

    def test_parser_fallback_finding_is_not_in_scope(self) -> None:
        """parse_findings emits file_path='unknown' when it cannot parse output."""
        finding = make_finding(file_path="unknown", line_reference="0")

        validate_findings([finding], files())

        assert finding.verification == "not_in_scope"


class TestPathResolution:
    def test_resolves_by_unique_basename(self) -> None:
        finding = make_finding(file_path="/some/other/root/auth.py")

        validate_findings([finding], files())

        assert finding.verification == "verified"

    def test_ambiguous_basename_is_not_guessed(self) -> None:
        entries = [
            FileEntry(path="a/auth.py", content=SAMPLE),
            FileEntry(path="b/auth.py", content=SAMPLE),
        ]
        finding = make_finding(file_path="somewhere/auth.py")

        validate_findings([finding], entries)

        assert finding.verification == "not_in_scope"

    def test_handles_windows_separators(self) -> None:
        finding = make_finding(file_path="app\\auth.py")

        validate_findings([finding], files())

        assert finding.verification == "verified"


class TestBehaviourContract:
    def test_findings_are_never_dropped(self) -> None:
        findings = [
            make_finding(id="f1"),
            make_finding(id="f2", file_path="nope.py"),
            make_finding(id="f3", line_reference="9999"),
        ]

        result = validate_findings(findings, files())

        assert len(result) == 3
        assert {f.id for f in result} == {"f1", "f2", "f3"}

    def test_counts_tally_by_status(self) -> None:
        findings = [
            make_finding(id="f1"),
            make_finding(id="f2", file_path="nope.py"),
            make_finding(id="f3", line_reference="9999"),
        ]
        validate_findings(findings, files())

        counts = verification_counts(findings)

        assert counts["verified"] == 1
        assert counts["not_in_scope"] == 1
        assert counts["unverified"] == 1

    def test_empty_file_list_marks_everything_out_of_scope(self) -> None:
        finding = make_finding()

        validate_findings([finding], [])

        assert finding.verification == "not_in_scope"
