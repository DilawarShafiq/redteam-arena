"""Tests for redteam_arena.agents.response_parser."""

from __future__ import annotations

import json

import pytest

from redteam_arena.agents.response_parser import parse_findings, parse_mitigations


# --- Helpers ---


def build_json_block(obj: object) -> str:
    return "```json\n" + json.dumps(obj, indent=2) + "\n```"


# --- parse_findings ---


class TestParseFindingsValidJsonBlock:
    def test_parses_a_single_finding_from_a_json_block(self) -> None:
        finding = {
            "filePath": "src/db.ts",
            "lineReference": "42",
            "description": "SQL injection via concatenation",
            "attackVector": "User-controlled input in raw SQL",
            "severity": "high",
        }
        raw = "Analysis complete.\n\n" + build_json_block([finding])

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert len(result.value) == 1
        assert result.value[0].description == "SQL injection via concatenation"
        assert result.value[0].severity == "high"
        assert result.value[0].file_path == "src/db.ts"
        assert result.value[0].line_reference == "42"
        assert result.value[0].attack_vector == "User-controlled input in raw SQL"

    def test_assigns_the_correct_round_number(self) -> None:
        finding = {
            "filePath": "src/auth.ts",
            "lineReference": "10",
            "description": "Auth bypass",
            "attackVector": "Missing check",
            "severity": "critical",
        }
        raw = build_json_block([finding])

        result = parse_findings(raw, 3)

        assert result.ok is True
        assert result.value[0].round_number == 3

    def test_assigns_a_non_empty_id(self) -> None:
        finding = {
            "filePath": "src/api.ts",
            "lineReference": "5",
            "description": "Unvalidated redirect",
            "attackVector": "Open redirect",
            "severity": "medium",
        }
        raw = build_json_block([finding])

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert isinstance(result.value[0].id, str)
        assert len(result.value[0].id) > 0

    def test_handles_unknown_severity_by_defaulting_to_medium(self) -> None:
        finding = {
            "filePath": "src/x.ts",
            "lineReference": "1",
            "description": "Some issue",
            "attackVector": "Some vector",
            "severity": "super-critical-ultra",
        }
        raw = build_json_block([finding])

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert result.value[0].severity == "medium"

    def test_parses_code_snippet_when_provided(self) -> None:
        finding = {
            "filePath": "src/db.ts",
            "lineReference": "99",
            "description": "Snippet test",
            "attackVector": "Direct injection",
            "severity": "high",
            "codeSnippet": 'query("SELECT * FROM users WHERE id=" + id)',
        }
        raw = build_json_block([finding])

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert result.value[0].code_snippet == 'query("SELECT * FROM users WHERE id=" + id)'

    def test_returns_ok_with_empty_array_for_empty_json_block(self) -> None:
        raw = build_json_block([])

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert len(result.value) == 0


class TestParseFindingsNoJsonBlocks:
    def test_returns_ok_with_single_fallback_finding(self) -> None:
        raw = "The code has an issue with authentication at line 50."

        result = parse_findings(raw, 2)

        assert result.ok is True
        assert len(result.value) == 1

    def test_fallback_finding_contains_slice_of_raw_output(self) -> None:
        raw = "No structured data here -- just free text analysis."

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert "No structured data here" in result.value[0].description

    def test_fallback_finding_has_correct_round_number(self) -> None:
        raw = "Plain text only."

        result = parse_findings(raw, 5)

        assert result.ok is True
        assert result.value[0].round_number == 5

    def test_fallback_finding_defaults_severity_to_medium(self) -> None:
        raw = "Something suspicious was found."

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert result.value[0].severity == "medium"

    def test_fallback_finding_has_file_path_unknown(self) -> None:
        raw = "An issue was detected."

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert result.value[0].file_path == "unknown"


class TestParseFindingsMultipleJsonBlocks:
    def test_parses_from_multiple_blocks_and_merges(self) -> None:
        block1 = build_json_block([
            {
                "filePath": "a.ts",
                "lineReference": "1",
                "description": "Issue A",
                "attackVector": "Vector A",
                "severity": "high",
            },
        ])
        block2 = build_json_block([
            {
                "filePath": "b.ts",
                "lineReference": "2",
                "description": "Issue B",
                "attackVector": "Vector B",
                "severity": "low",
            },
            {
                "filePath": "c.ts",
                "lineReference": "3",
                "description": "Issue C",
                "attackVector": "Vector C",
                "severity": "critical",
            },
        ])
        raw = "First block:\n" + block1 + "\n\nSecond block:\n" + block2

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert len(result.value) == 3

        descriptions = [f.description for f in result.value]
        assert "Issue A" in descriptions
        assert "Issue B" in descriptions
        assert "Issue C" in descriptions

    def test_skips_malformed_json_blocks_and_continues(self) -> None:
        bad_block = "```json\n{ this is not valid json }\n```"
        good_block = build_json_block([
            {
                "filePath": "ok.ts",
                "lineReference": "10",
                "description": "Valid finding",
                "attackVector": "Real vector",
                "severity": "medium",
            },
        ])
        raw = bad_block + "\n\n" + good_block

        result = parse_findings(raw, 1)

        assert result.ok is True
        assert len(result.value) >= 1
        valid_finding = next(
            (f for f in result.value if f.description == "Valid finding"), None
        )
        assert valid_finding is not None

    def test_each_finding_gets_unique_id(self) -> None:
        block = build_json_block([
            {
                "filePath": "a.ts",
                "lineReference": "1",
                "description": "A",
                "attackVector": "V",
                "severity": "low",
            },
            {
                "filePath": "b.ts",
                "lineReference": "2",
                "description": "B",
                "attackVector": "V",
                "severity": "low",
            },
        ])

        result = parse_findings(block, 1)

        assert result.ok is True
        ids = [f.id for f in result.value]
        assert len(set(ids)) == len(ids)


# --- parse_mitigations ---


class TestParseMitigationsValidJsonBlock:
    def test_parses_a_single_mitigation(self) -> None:
        mit = {
            "findingId": "find-001",
            "acknowledgment": "Confirmed SQL injection",
            "proposedFix": "Use parameterized queries",
            "confidence": "high",
        }
        raw = "Defense analysis:\n\n" + build_json_block([mit])
        finding_ids = ["find-001"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        assert len(result.value) >= 1
        m = next((x for x in result.value if x.finding_id == "find-001"), None)
        assert m is not None
        assert m.proposed_fix == "Use parameterized queries"
        assert m.confidence == "high"

    def test_sets_round_number_on_each_mitigation(self) -> None:
        mit = {
            "findingId": "find-001",
            "acknowledgment": "Ack",
            "proposedFix": "Fix",
            "confidence": "medium",
        }
        raw = build_json_block([mit])

        result = parse_mitigations(raw, 4, ["find-001"])

        assert result.ok is True
        assert result.value[0].round_number == 4

    def test_assigns_a_non_empty_id(self) -> None:
        mit = {
            "findingId": "find-abc",
            "acknowledgment": "Ack",
            "proposedFix": "Fix it",
            "confidence": "low",
        }
        raw = build_json_block([mit])

        result = parse_mitigations(raw, 1, ["find-abc"])

        assert result.ok is True
        assert isinstance(result.value[0].id, str)
        assert len(result.value[0].id) > 0

    def test_defaults_confidence_to_medium_for_unknown(self) -> None:
        mit = {
            "findingId": "find-001",
            "acknowledgment": "Ack",
            "proposedFix": "Fix",
            "confidence": "extreme",
        }
        raw = build_json_block([mit])

        result = parse_mitigations(raw, 1, ["find-001"])

        assert result.ok is True
        assert result.value[0].confidence == "medium"


class TestParseMitigationsMatchingFindingIds:
    def test_creates_one_per_finding_id_with_no_json_blocks(self) -> None:
        raw = "I have reviewed the findings and here are my recommendations."
        finding_ids = ["f1", "f2", "f3"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        assert len(result.value) == 3

    def test_fallback_references_corresponding_finding_ids(self) -> None:
        raw = "General mitigation advice for all findings."
        finding_ids = ["find-A", "find-B"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        ids = [m.finding_id for m in result.value]
        assert "find-A" in ids
        assert "find-B" in ids

    def test_fills_gaps_when_fewer_mitigations_than_findings(self) -> None:
        mit = {
            "findingId": "f1",
            "acknowledgment": "Ack",
            "proposedFix": "Fix for f1",
            "confidence": "high",
        }
        raw = build_json_block([mit])
        finding_ids = ["f1", "f2", "f3"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        assert len(result.value) == 3

        finding_id_set = {m.finding_id for m in result.value}
        assert "f1" in finding_id_set

    def test_returns_ok_with_empty_when_finding_ids_empty_and_no_json(self) -> None:
        raw = "Nothing to mitigate."

        result = parse_mitigations(raw, 1, [])

        assert result.ok is True
        assert len(result.value) == 0

    def test_uses_finding_id_from_json_when_provided(self) -> None:
        mit = {
            "findingId": "explicit-id-999",
            "acknowledgment": "Confirmed",
            "proposedFix": "Fix explicitly",
            "confidence": "high",
        }
        raw = build_json_block([mit])
        finding_ids = ["explicit-id-999", "other-id"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        assert result.value[0].finding_id == "explicit-id-999"


class TestParseMitigationsFallback:
    def test_fallback_contains_slice_of_raw_text(self) -> None:
        raw = "Apply input validation and use prepared statements throughout the codebase."
        finding_ids = ["f1"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        assert "Apply input validation" in result.value[0].proposed_fix

    def test_fallback_has_acknowledged(self) -> None:
        raw = "General advice here."
        finding_ids = ["f1"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        assert result.value[0].acknowledgment == "Acknowledged"

    def test_fallback_defaults_confidence_to_medium(self) -> None:
        raw = "Some advice."
        finding_ids = ["f1"]

        result = parse_mitigations(raw, 1, finding_ids)

        assert result.ok is True
        assert result.value[0].confidence == "medium"
