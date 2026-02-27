"""
Smoke tests for the CLI entry points.
Uses Click's CliRunner to invoke commands without a live LLM.
"""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from redteam_arena.cli import cli


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


class TestVersion:
    def test_version_flag(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "0.0.1" in result.output


class TestHelp:
    def test_root_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "battle" in result.output
        assert "list" in result.output
        assert "serve" in result.output
        assert "watch" in result.output
        assert "benchmark" in result.output
        assert "history" in result.output
        assert "dashboard" in result.output

    def test_battle_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["battle", "--help"])
        assert result.exit_code == 0
        assert "--scenario" in result.output
        assert "--rounds" in result.output
        assert "--provider" in result.output
        assert "--format" in result.output
        assert "--fail-on" in result.output

    def test_list_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0
        assert "--tag" in result.output

    def test_serve_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--port" in result.output

    def test_watch_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["watch", "--help"])
        assert result.exit_code == 0
        assert "--scenario" in result.output

    def test_benchmark_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["benchmark", "--help"])
        assert result.exit_code == 0
        assert "--suite" in result.output

    def test_history_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["history", "--help"])
        assert result.exit_code == 0
        assert "--trends" in result.output

    def test_dashboard_help(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["dashboard", "--help"])
        assert result.exit_code == 0
        assert "--output" in result.output


class TestListCommand:
    def test_list_scenarios(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "sql-injection" in result.output
        assert "xss" in result.output
        assert "prompt-injection" in result.output
        assert "full-audit" in result.output

    def test_list_shows_count(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        assert "scenario(s) available" in result.output

    def test_list_benchmark_suites(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["benchmark", "--list-suites"])
        assert result.exit_code == 0


class TestBattleValidation:
    def test_battle_requires_scenario(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["battle", "."])
        assert result.exit_code != 0
        assert "scenario" in result.output.lower() or "Missing option" in result.output

    def test_battle_unknown_directory(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["battle", "/nonexistent/path", "--scenario", "xss"])
        # Should exit non-zero because directory not found
        assert result.exit_code != 0

    def test_battle_invalid_format(self, runner: CliRunner) -> None:
        result = runner.invoke(cli, ["battle", ".", "--scenario", "xss", "--format", "invalid"])
        assert result.exit_code != 0
