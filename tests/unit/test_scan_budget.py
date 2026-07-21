"""Tests for the configurable scan budget.

Raising the budget must widen coverage of a large tree in a single pass, and
the BattleConfig field must flow into the reader. There is no multi-pass cost
multiplier -- one battle, one prompt, bounded by the model's context window.
"""

from __future__ import annotations

import os
import shutil
import tempfile

import pytest

from redteam_arena.core.config import _validate_config
from redteam_arena.core.file_reader import read_codebase
from redteam_arena.types import ScanScope

_temp_dirs: list[str] = []


def big_tree(file_count: int, kb_each: int) -> str:
    d = tempfile.mkdtemp(prefix="scan-budget-")
    _temp_dirs.append(d)
    line = "x = 1  # padding to size\n"
    reps = (kb_each * 1024) // len(line)
    for i in range(file_count):
        with open(os.path.join(d, f"file{i:02d}.py"), "w", encoding="utf-8") as f:
            f.write(line * reps)
    return d


@pytest.fixture(autouse=True)
def cleanup():
    yield
    for d in _temp_dirs[:]:
        shutil.rmtree(d, ignore_errors=True)
    _temp_dirs.clear()


class TestBudgetWidensCoverage:
    @pytest.mark.asyncio
    async def test_small_budget_is_partial(self) -> None:
        d = big_tree(8, kb_each=30)  # ~240KB
        scope = ScanScope()

        await read_codebase(d, max_file_size=100 * 1024, max_total_size=100 * 1024, scope=scope)

        assert scope.is_partial is True
        assert scope.files_read < 8

    @pytest.mark.asyncio
    async def test_large_budget_covers_everything(self) -> None:
        d = big_tree(8, kb_each=30)  # ~240KB
        scope = ScanScope()

        await read_codebase(d, max_file_size=400 * 1024, max_total_size=400 * 1024, scope=scope)

        assert scope.files_read == 8
        assert scope.is_partial is False

    @pytest.mark.asyncio
    async def test_raised_budget_reads_a_large_single_file(self) -> None:
        """A file bigger than the old 64KB per-file cap is read when budget allows."""
        d = big_tree(1, kb_each=120)  # one 120KB file
        scope = ScanScope()

        await read_codebase(d, max_file_size=200 * 1024, max_total_size=200 * 1024, scope=scope)

        assert scope.files_read == 1
        assert scope.skipped_count == 0


class TestConfigFileParsing:
    def test_reads_camel_case_key(self) -> None:
        cfg = _validate_config({"maxScanKb": 500})

        assert cfg.max_scan_kb == 500

    def test_reads_snake_case_key(self) -> None:
        cfg = _validate_config({"max_scan_kb": 250})

        assert cfg.max_scan_kb == 250

    def test_ignores_invalid_value(self) -> None:
        cfg = _validate_config({"maxScanKb": -5})

        assert cfg.max_scan_kb is None

    def test_absent_key_is_none(self) -> None:
        cfg = _validate_config({})

        assert cfg.max_scan_kb is None


class TestBattleConfigWiring:
    @pytest.mark.asyncio
    async def test_engine_uses_config_budget(self) -> None:
        """A raised max_scan_bytes on BattleConfig reaches the reader."""
        from redteam_arena.agents.blue_agent import BlueAgent
        from redteam_arena.agents.mock_provider import MockProvider
        from redteam_arena.agents.red_agent import RedAgent
        from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
        from redteam_arena.types import BattleConfig, Scenario

        d = big_tree(8, kb_each=30)  # ~240KB, exceeds the 100KB default
        scenario = Scenario(
            name="s", description="d", focus_areas=[],
            severity_guidance="", red_guidance="", blue_guidance="",
            is_meta=False, sub_scenarios=[],
        )
        provider = MockProvider()
        config = BattleConfig(
            target_dir=d, scenario=scenario, rounds=1,
            max_scan_bytes=400 * 1024,
        )
        engine = BattleEngine(
            BattleEngineOptions(
                red_agent=RedAgent(provider),
                blue_agent=BlueAgent(provider),
                config=config,
            )
        )

        battle = await engine.run()

        assert battle.scan_scope is not None
        assert battle.scan_scope.files_read == 8
        assert battle.scan_scope.is_partial is False
