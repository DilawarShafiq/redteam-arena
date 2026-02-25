"""Integration tests for the battle engine flow."""

from __future__ import annotations

import asyncio
import os
import shutil
import tempfile
from collections.abc import AsyncIterator

import pytest

from redteam_arena.agents.agent import Agent
from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
from redteam_arena.types import AgentContext, BattleConfig, Scenario


# Mock agent that returns predictable output


class MockRedAgent(Agent):
    async def analyze(self, context: AgentContext) -> AsyncIterator[str]:
        output = """I found a vulnerability in the code.

```json
[
  {
    "filePath": "app.ts",
    "lineReference": "5",
    "description": "Hardcoded secret found",
    "attackVector": "Token forgery",
    "severity": "high",
    "codeSnippet": "const SECRET = 'abc123'"
  }
]
```"""
        yield output


class MockBlueAgent(Agent):
    async def analyze(self, context: AgentContext) -> AsyncIterator[str]:
        output = """I acknowledge the finding and propose a fix.

```json
[
  {
    "acknowledgment": "Valid finding - hardcoded secret detected",
    "proposedFix": "Move to environment variable: process.env.SECRET",
    "confidence": "high"
  }
]
```"""
        yield output


MOCK_SCENARIO = Scenario(
    name="test-scenario",
    description="Test scenario",
    focus_areas=["hardcoded secrets"],
    severity_guidance="High for any hardcoded secret",
    red_guidance="Find secrets",
    blue_guidance="Fix secrets",
)


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp(prefix="battle-test-")
    with open(os.path.join(d, "app.ts"), "w", encoding="utf-8") as f:
        f.write('const SECRET = "abc123";\nexport function getSecret() { return SECRET; }\n')
    yield d
    shutil.rmtree(d, ignore_errors=True)


class TestBattleFlowIntegration:
    @pytest.mark.asyncio
    async def test_runs_complete_battle_with_mock_agents(self, temp_dir: str) -> None:
        config = BattleConfig(
            target_dir=temp_dir,
            scenario=MOCK_SCENARIO,
            rounds=2,
        )

        engine = BattleEngine(
            BattleEngineOptions(
                red_agent=MockRedAgent(),
                blue_agent=MockBlueAgent(),
                config=config,
            )
        )

        battle = await engine.run()

        assert battle.status == "completed"
        assert len(battle.rounds) == 2
        assert battle.id
        assert battle.started_at is not None
        assert battle.ended_at is not None

    @pytest.mark.asyncio
    async def test_emits_events_in_correct_order(self, temp_dir: str) -> None:
        config = BattleConfig(
            target_dir=temp_dir,
            scenario=MOCK_SCENARIO,
            rounds=1,
        )

        engine = BattleEngine(
            BattleEngineOptions(
                red_agent=MockRedAgent(),
                blue_agent=MockBlueAgent(),
                config=config,
            )
        )

        battle = await engine.run()
        event_types = [e.type for e in battle.events]

        assert event_types[0] == "battle-start"
        assert event_types[1] == "round-start"
        assert event_types[2] == "attack"
        assert event_types[3] == "defend"
        assert event_types[4] == "round-end"
        assert event_types[-1] == "battle-end"

    @pytest.mark.asyncio
    async def test_collects_findings_and_mitigations(self, temp_dir: str) -> None:
        config = BattleConfig(
            target_dir=temp_dir,
            scenario=MOCK_SCENARIO,
            rounds=1,
        )

        engine = BattleEngine(
            BattleEngineOptions(
                red_agent=MockRedAgent(),
                blue_agent=MockBlueAgent(),
                config=config,
            )
        )

        battle = await engine.run()
        rnd = battle.rounds[0]

        assert len(rnd.findings) > 0
        assert rnd.findings[0].severity == "high"
        assert rnd.findings[0].file_path == "app.ts"
        assert len(rnd.mitigations) > 0

    @pytest.mark.asyncio
    async def test_handles_interruption_gracefully(self, temp_dir: str) -> None:

        class SlowRedAgent(Agent):
            async def analyze(self, context: AgentContext) -> AsyncIterator[str]:
                yield "Analyzing..."
                await asyncio.sleep(0.1)
                yield '\n```json\n[{"filePath":"a.ts","lineReference":"1","description":"test","attackVector":"test","severity":"high"}]\n```'

        config = BattleConfig(
            target_dir=temp_dir,
            scenario=MOCK_SCENARIO,
            rounds=10,
        )

        engine = BattleEngine(
            BattleEngineOptions(
                red_agent=SlowRedAgent(),
                blue_agent=MockBlueAgent(),
                config=config,
            )
        )

        # Schedule interrupt after a short delay
        async def interrupt_later():
            await asyncio.sleep(0.15)
            engine.interrupt()

        asyncio.create_task(interrupt_later())

        battle = await engine.run()

        assert battle.status == "interrupted"
        assert len(battle.rounds) < 10

    @pytest.mark.asyncio
    async def test_error_when_target_has_no_source_files(self) -> None:
        empty_dir = tempfile.mkdtemp(prefix="empty-test-")

        config = BattleConfig(
            target_dir=empty_dir,
            scenario=MOCK_SCENARIO,
            rounds=1,
        )

        engine = BattleEngine(
            BattleEngineOptions(
                red_agent=MockRedAgent(),
                blue_agent=MockBlueAgent(),
                config=config,
            )
        )

        with pytest.raises(RuntimeError, match="No source files found"):
            await engine.run()

        shutil.rmtree(empty_dir, ignore_errors=True)
