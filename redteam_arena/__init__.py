"""
RedTeam Arena -- AI vs AI adversarial security testing.
Programmatic API entry point.
"""

from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
from redteam_arena.core.event_system import BattleEventSystem
from redteam_arena.core.file_reader import read_codebase, format_files_for_prompt, has_source_files
from redteam_arena.agents.claude_adapter import ClaudeAdapter, validate_api_key
from redteam_arena.agents.red_agent import RedAgent
from redteam_arena.agents.blue_agent import BlueAgent
from redteam_arena.agents.response_parser import parse_findings, parse_mitigations
from redteam_arena.scenarios.scenario import load_scenario, list_scenarios
from redteam_arena.reports.battle_report import generate_report, write_report
from redteam_arena.types import (
    Battle,
    BattleConfig,
    BattleEvent,
    BattleStatus,
    BattleSummary,
    Finding,
    Mitigation,
    Round,
    Scenario,
    Severity,
    FileEntry,
    AgentContext,
    StreamOptions,
    Message,
    Result,
)
from redteam_arena.agents.agent import Agent
from redteam_arena.agents.provider import Provider

__all__ = [
    "BattleEngine",
    "BattleEngineOptions",
    "BattleEventSystem",
    "read_codebase",
    "format_files_for_prompt",
    "has_source_files",
    "ClaudeAdapter",
    "validate_api_key",
    "RedAgent",
    "BlueAgent",
    "parse_findings",
    "parse_mitigations",
    "load_scenario",
    "list_scenarios",
    "generate_report",
    "write_report",
    "Battle",
    "BattleConfig",
    "BattleEvent",
    "BattleStatus",
    "BattleSummary",
    "Finding",
    "Mitigation",
    "Round",
    "Scenario",
    "Severity",
    "FileEntry",
    "AgentContext",
    "StreamOptions",
    "Message",
    "Result",
    "Agent",
    "Provider",
]
