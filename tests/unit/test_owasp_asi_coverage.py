"""Tests for OWASP Agentic Top 10 (2026) scenario coverage.

Complete ASI coverage is the project's clearest differentiator, so it is worth
a test that fails loudly if a scenario is renamed, retagged, or dropped.
"""

from __future__ import annotations

import pytest

from redteam_arena.scenarios.scenario import list_scenarios, load_scenario

# OWASP Top 10 for Agentic Applications 2026, published December 2025.
EXPECTED: dict[str, str] = {
    "ASI01": "agent-goal-hijack",
    "ASI02": "tool-misuse",
    "ASI03": "identity-privilege-abuse",
    "ASI04": "agentic-supply-chain",
    "ASI05": "unexpected-code-execution",
    "ASI06": "memory-poisoning",
    "ASI07": "insecure-inter-agent-comms",
    "ASI08": "cascading-failures",
    "ASI09": "human-agent-trust",
    "ASI10": "rogue-agents",
}


class TestAsiCoverage:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("asi", "slug"), sorted(EXPECTED.items()))
    async def test_scenario_declares_its_asi_id(self, asi: str, slug: str) -> None:
        result = await load_scenario(slug)

        assert result.ok is True, f"{slug} failed to load"
        assert result.value.owasp_asi == asi

    @pytest.mark.asyncio
    async def test_all_ten_are_covered(self) -> None:
        scenarios = await list_scenarios()

        covered = {s.owasp_asi for s in scenarios if s.owasp_asi}

        assert covered == set(EXPECTED), f"Missing: {set(EXPECTED) - covered}"

    @pytest.mark.asyncio
    async def test_no_duplicate_asi_assignments(self) -> None:
        scenarios = await list_scenarios()

        assigned = [s.owasp_asi for s in scenarios if s.owasp_asi]

        assert len(assigned) == len(set(assigned)), "An ASI ID is claimed twice"

    @pytest.mark.asyncio
    async def test_non_agentic_scenarios_have_no_asi_id(self) -> None:
        result = await load_scenario("sql-injection")

        assert result.value.owasp_asi == ""
