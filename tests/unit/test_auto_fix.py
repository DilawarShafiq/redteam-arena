"""Tests for redteam_arena.core.auto_fix.

This module runs git against a user's working tree, so the safety properties
matter more than the happy path: it must not touch git unless asked, must not
commit to the wrong branch when a git call fails, and must always put the user
back on the branch they started on.
"""

from __future__ import annotations

import asyncio
import os
import shutil
import subprocess
import tempfile
from datetime import datetime

import pytest

from redteam_arena.core.auto_fix import (
    format_auto_fix_summary,
    run_auto_fix,
)
from redteam_arena.types import (
    Battle,
    BattleConfig,
    Finding,
    Mitigation,
    Round,
    Scenario,
)

_temp_dirs: list[str] = []


def create_temp_dir() -> str:
    d = tempfile.mkdtemp(prefix="auto-fix-test-")
    _temp_dirs.append(d)
    return d


def init_repo() -> str:
    """A git repo with one commit, on a known branch."""
    d = create_temp_dir()

    def run(*a: str) -> None:
        subprocess.run(["git", *a], cwd=d, capture_output=True, check=True)

    run("init", "-b", "main")
    run("config", "user.email", "test@example.com")
    run("config", "user.name", "Test")
    with open(os.path.join(d, "app.py"), "w", encoding="utf-8") as f:
        f.write("x = 1\n")
    run("add", ".")
    run("commit", "-m", "initial")
    return d


def current_branch(d: str) -> str:
    return subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=d, capture_output=True, text=True, check=True,
    ).stdout.strip()


def branches(d: str) -> list[str]:
    out = subprocess.run(
        ["git", "branch", "--format=%(refname:short)"],
        cwd=d, capture_output=True, text=True, check=True,
    ).stdout
    return [b.strip() for b in out.splitlines() if b.strip()]


@pytest.fixture(autouse=True)
def cleanup_temp_dirs():
    yield
    for d in _temp_dirs[:]:
        try:
            shutil.rmtree(d, ignore_errors=True)
        except OSError:
            pass
    _temp_dirs.clear()


def make_battle(n: int = 2) -> Battle:
    findings, mitigations = [], []
    for i in range(n):
        fid = f"find-{i}"
        findings.append(
            Finding(
                id=fid,
                round_number=1,
                file_path="app.py",
                line_reference="1",
                description=f"Issue number {i}",
                attack_vector="vector",
                severity="high",
            )
        )
        mitigations.append(
            Mitigation(
                id=f"mit-{i}",
                finding_id=fid,
                round_number=1,
                acknowledgment="confirmed",
                proposed_fix="Use parameterized queries",
                confidence="high",
            )
        )
    return Battle(
        id="battle-1",
        config=BattleConfig(
            target_dir=".",
            scenario=Scenario(
                name="s", description="d", focus_areas=[],
                severity_guidance="", red_guidance="", blue_guidance="",
                is_meta=False, sub_scenarios=[],
            ),
            rounds=1,
        ),
        rounds=[Round(number=1, findings=findings, mitigations=mitigations,
                      red_raw_output="", blue_raw_output="")],
        events=[],
        status="completed",
        started_at=datetime(2026, 7, 21, 9, 0, 0),
    )


class TestDoesNotTouchGitByDefault:
    """Writing to a user's repo is a side effect they must opt into."""

    @pytest.mark.asyncio
    async def test_creates_no_branches_by_default(self) -> None:
        d = init_repo()

        result = await run_auto_fix(d, make_battle())

        assert result.ok is True
        assert branches(d) == ["main"]

    @pytest.mark.asyncio
    async def test_makes_no_commits_by_default(self) -> None:
        d = init_repo()
        before = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True, check=True
        ).stdout

        await run_auto_fix(d, make_battle())

        after = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=d, capture_output=True, text=True, check=True
        ).stdout
        assert before == after

    @pytest.mark.asyncio
    async def test_works_outside_a_git_repo(self) -> None:
        d = create_temp_dir()

        result = await run_auto_fix(d, make_battle())

        assert result.ok is True
        assert result.value.proposals_written == 2

    @pytest.mark.asyncio
    async def test_writes_proposal_files(self) -> None:
        d = create_temp_dir()

        result = await run_auto_fix(d, make_battle())

        for fix in result.value.fixes:
            assert os.path.isfile(fix.proposal_path)

    @pytest.mark.asyncio
    async def test_does_not_modify_source_files(self) -> None:
        d = init_repo()
        source = os.path.join(d, "app.py")
        original = open(source, encoding="utf-8").read()

        await run_auto_fix(d, make_battle())

        assert open(source, encoding="utf-8").read() == original


class TestBranchMode:
    @pytest.mark.asyncio
    async def test_creates_one_branch_per_finding(self) -> None:
        d = init_repo()

        await run_auto_fix(d, make_battle(2), create_branch=True)

        assert len([b for b in branches(d) if b.startswith("fix/redteam-")]) == 2

    @pytest.mark.asyncio
    async def test_restores_original_branch(self) -> None:
        d = init_repo()

        await run_auto_fix(d, make_battle(2), create_branch=True)

        assert current_branch(d) == "main"

    @pytest.mark.asyncio
    async def test_refuses_dirty_working_tree(self) -> None:
        d = init_repo()
        with open(os.path.join(d, "app.py"), "a", encoding="utf-8") as f:
            f.write("dirty = True\n")

        result = await run_auto_fix(d, make_battle(), create_branch=True)

        assert result.ok is False
        assert "uncommitted changes" in str(result.error)

    @pytest.mark.asyncio
    async def test_refuses_non_git_directory(self) -> None:
        d = create_temp_dir()

        result = await run_auto_fix(d, make_battle(), create_branch=True)

        assert result.ok is False
        assert "not a git repository" in str(result.error)

    @pytest.mark.asyncio
    async def test_branch_failure_does_not_commit_to_base(self) -> None:
        """Regression: unchecked git calls let a failed checkout commit to main."""
        d = init_repo()
        battle = make_battle(1)
        finding = battle.rounds[0].findings[0]
        # Pre-create the branch so `checkout -b` fails.
        subprocess.run(
            ["git", "branch",
             f"fix/redteam-{finding.id}-issue-number-0"],
            cwd=d, capture_output=True, check=True,
        )
        head_before = subprocess.run(
            ["git", "rev-parse", "main"], cwd=d, capture_output=True, text=True, check=True
        ).stdout

        result = await run_auto_fix(d, battle, create_branch=True)

        head_after = subprocess.run(
            ["git", "rev-parse", "main"], cwd=d, capture_output=True, text=True, check=True
        ).stdout
        assert head_before == head_after, "a failed checkout must not commit to the base branch"
        assert result.value.proposals_written == 0
        assert current_branch(d) == "main"


class TestDryRun:
    @pytest.mark.asyncio
    async def test_writes_nothing(self) -> None:
        d = init_repo()

        result = await run_auto_fix(d, make_battle(), create_branch=True, dry_run=True)

        assert result.value.proposals_written == 0
        assert branches(d) == ["main"]
        assert not os.path.exists(os.path.join(d, ".redteam-fixes"))


class TestSummaryHonesty:
    def test_summary_does_not_claim_fixes_were_applied(self) -> None:
        d = create_temp_dir()
        summary = asyncio.run(run_auto_fix(d, make_battle())).value

        text = format_auto_fix_summary(summary)

        assert "not applied changes" in text
        assert "No source" in text
        assert "Applied:" not in text
