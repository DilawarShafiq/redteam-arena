"""Tests for redteam_arena.reports.sarif_reporter.

The point of these is the GitHub code-scanning contract: rule IDs and
fingerprints must be stable across runs (so alerts persist and dismissals
stick), paths must resolve against the repo root, and the document must be
structurally valid SARIF.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime

import pytest

from redteam_arena.reports.sarif_reporter import generate_sarif_report
from redteam_arena.types import (
    Battle,
    BattleConfig,
    Finding,
    Round,
    Scenario,
)

_temp_dirs: list[str] = []


def create_temp_dir() -> str:
    d = tempfile.mkdtemp(prefix="sarif-test-")
    _temp_dirs.append(d)
    return d


@pytest.fixture(autouse=True)
def cleanup():
    yield
    for d in _temp_dirs[:]:
        shutil.rmtree(d, ignore_errors=True)
    _temp_dirs.clear()


def make_finding(desc: str, **kw: object) -> Finding:
    defaults = dict(
        id="f1",
        round_number=1,
        file_path="src/auth.py",
        line_reference="42",
        description=desc,
        attack_vector="v",
        severity="high",
    )
    defaults.update(kw)
    return Finding(**defaults)  # type: ignore[arg-type]


def make_battle(findings: list[Finding], target_dir: str = "/repo") -> Battle:
    return Battle(
        id="b1",
        config=BattleConfig(
            target_dir=target_dir,
            scenario=Scenario(
                name="sql-injection", description="Find SQL injection",
                focus_areas=[], severity_guidance="",
                red_guidance="", blue_guidance="",
                is_meta=False, sub_scenarios=[],
            ),
            rounds=1,
        ),
        rounds=[Round(number=1, findings=findings, mitigations=[],
                      red_raw_output="", blue_raw_output="")],
        events=[],
        status="completed",
        started_at=datetime(2026, 7, 21),
    )


class TestValidStructure:
    def test_is_valid_json_sarif_210(self) -> None:
        doc = json.loads(generate_sarif_report(make_battle([make_finding("x")])))

        assert doc["version"] == "2.1.0"
        assert doc["runs"][0]["tool"]["driver"]["name"] == "redteam-arena"

    def test_no_malformed_uribaseid(self) -> None:
        raw = generate_sarif_report(make_battle([make_finding("x")]))

        # The old %SRCROOT% delimiter form is invalid as a uriBaseId value.
        assert "%SRCROOT%" not in raw


class TestStableRuleIds:
    def test_rule_id_ignores_description_wording(self) -> None:
        a = json.loads(generate_sarif_report(make_battle([make_finding("Tautology login bypass")])))
        b = json.loads(generate_sarif_report(make_battle([make_finding("Auth bypass via always-true WHERE")])))

        assert a["runs"][0]["results"][0]["ruleId"] == b["runs"][0]["results"][0]["ruleId"]

    def test_rule_id_derives_from_scenario(self) -> None:
        doc = json.loads(generate_sarif_report(make_battle([make_finding("x")])))

        assert doc["runs"][0]["results"][0]["ruleId"] == "redteam-arena/sql-injection"


class TestStableFingerprints:
    def test_fingerprint_stable_across_reword(self) -> None:
        a = json.loads(generate_sarif_report(make_battle([make_finding("first wording")])))
        b = json.loads(generate_sarif_report(make_battle([make_finding("totally different wording")])))

        fa = a["runs"][0]["results"][0]["partialFingerprints"]["primaryLocationLineHash"]
        fb = b["runs"][0]["results"][0]["partialFingerprints"]["primaryLocationLineHash"]
        assert fa == fb

    def test_fingerprint_differs_by_location(self) -> None:
        a = json.loads(generate_sarif_report(make_battle([make_finding("x", file_path="a.py")])))
        b = json.loads(generate_sarif_report(make_battle([make_finding("x", file_path="b.py")])))

        fa = a["runs"][0]["results"][0]["partialFingerprints"]["primaryLocationLineHash"]
        fb = b["runs"][0]["results"][0]["partialFingerprints"]["primaryLocationLineHash"]
        assert fa != fb

    def test_whole_document_is_byte_identical_across_runs(self) -> None:
        battle = make_battle([make_finding("x"), make_finding("y", id="f2", file_path="src/db.py")])

        assert generate_sarif_report(battle) == generate_sarif_report(battle)


class TestRepoRelativePaths:
    def test_path_prefixed_by_target_offset_in_repo(self) -> None:
        repo = create_temp_dir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)
        src = os.path.join(repo, "backend")
        os.makedirs(src)

        doc = json.loads(generate_sarif_report(make_battle([make_finding("x")], target_dir=src)))
        uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]

        assert uri == "backend/src/auth.py"

    def test_repo_root_target_has_no_prefix(self) -> None:
        repo = create_temp_dir()
        subprocess.run(["git", "init"], cwd=repo, capture_output=True, check=True)

        doc = json.loads(generate_sarif_report(make_battle([make_finding("x")], target_dir=repo)))
        uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]

        assert uri == "src/auth.py"

    def test_no_git_repo_leaves_path_as_is(self) -> None:
        plain = create_temp_dir()

        doc = json.loads(generate_sarif_report(make_battle([make_finding("x")], target_dir=plain)))
        uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]

        assert uri == "src/auth.py"

    def test_windows_separators_normalized(self) -> None:
        doc = json.loads(generate_sarif_report(
            make_battle([make_finding("x", file_path="src\\auth.py")], target_dir="/nope")
        ))
        uri = doc["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"]

        assert "\\" not in uri


class TestVersion:
    def test_semantic_version_tracks_package(self) -> None:
        from redteam_arena import __version__

        doc = json.loads(generate_sarif_report(make_battle([make_finding("x")])))

        assert doc["runs"][0]["tool"]["driver"]["semanticVersion"] == __version__
