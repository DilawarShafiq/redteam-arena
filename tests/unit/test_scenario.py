"""Tests for redteam_arena.scenarios.scenario."""

from __future__ import annotations

import pytest

from redteam_arena.scenarios.scenario import load_scenario, list_scenarios


class TestLoadScenario:
    @pytest.mark.asyncio
    async def test_loads_valid_scenario_without_error(self) -> None:
        result = await load_scenario("sql-injection")
        assert result.ok is True

    @pytest.mark.asyncio
    async def test_loaded_scenario_has_expected_fields(self) -> None:
        result = await load_scenario("sql-injection")
        assert result.ok is True

        scenario = result.value
        assert hasattr(scenario, "name")
        assert hasattr(scenario, "description")
        assert hasattr(scenario, "focus_areas")
        assert hasattr(scenario, "red_guidance")
        assert hasattr(scenario, "blue_guidance")

    @pytest.mark.asyncio
    async def test_name_and_description_are_non_empty(self) -> None:
        result = await load_scenario("sql-injection")
        assert result.ok is True

        assert isinstance(result.value.name, str)
        assert len(result.value.name) > 0
        assert isinstance(result.value.description, str)
        assert len(result.value.description) > 0

    @pytest.mark.asyncio
    async def test_focus_areas_is_non_empty_list(self) -> None:
        result = await load_scenario("sql-injection")
        assert result.ok is True

        assert isinstance(result.value.focus_areas, list)
        assert len(result.value.focus_areas) > 0

    @pytest.mark.asyncio
    async def test_red_guidance_has_content(self) -> None:
        result = await load_scenario("sql-injection")
        assert result.ok is True
        assert len(result.value.red_guidance) > 0

    @pytest.mark.asyncio
    async def test_blue_guidance_has_content(self) -> None:
        result = await load_scenario("sql-injection")
        assert result.ok is True
        assert len(result.value.blue_guidance) > 0

    @pytest.mark.asyncio
    async def test_error_for_nonexistent_scenario(self) -> None:
        result = await load_scenario("this-scenario-does-not-exist")
        assert result.ok is False
        assert isinstance(result.error, Exception)
        assert "not found" in str(result.error).lower()

    @pytest.mark.asyncio
    async def test_error_for_empty_scenario_name(self) -> None:
        result = await load_scenario("")
        assert result.ok is False


class TestListScenarios:
    @pytest.mark.asyncio
    async def test_returns_a_list(self) -> None:
        scenarios = await list_scenarios()
        assert isinstance(scenarios, list)

    @pytest.mark.asyncio
    async def test_returns_at_least_one_scenario(self) -> None:
        scenarios = await list_scenarios()
        assert len(scenarios) > 0

    @pytest.mark.asyncio
    async def test_each_scenario_has_required_fields(self) -> None:
        scenarios = await list_scenarios()

        for scenario in scenarios:
            assert hasattr(scenario, "name")
            assert hasattr(scenario, "description")
            assert hasattr(scenario, "focus_areas")
            assert hasattr(scenario, "red_guidance")
            assert hasattr(scenario, "blue_guidance")

    @pytest.mark.asyncio
    async def test_includes_sql_injection(self) -> None:
        scenarios = await list_scenarios()
        found = any(s.name == "sql-injection" for s in scenarios)
        assert found is True

    @pytest.mark.asyncio
    async def test_full_audit_is_meta_with_sub_scenarios(self) -> None:
        result = await load_scenario("full-audit")
        assert result.ok is True

        scenario = result.value
        assert scenario.is_meta is True
        assert isinstance(scenario.sub_scenarios, list)
        assert len(scenario.sub_scenarios) > 0

    @pytest.mark.asyncio
    async def test_full_audit_sub_scenarios_reference_known_names(self) -> None:
        result = await load_scenario("full-audit")
        assert result.ok is True
        assert "sql-injection" in result.value.sub_scenarios

    @pytest.mark.asyncio
    async def test_non_meta_scenarios_have_is_meta_false(self) -> None:
        result = await load_scenario("sql-injection")
        assert result.ok is True
        assert not result.value.is_meta
