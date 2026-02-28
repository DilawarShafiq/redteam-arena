"""
RedTeam Arena -- AI vs AI adversarial security testing.
Programmatic API entry point.
"""

__version__ = "0.0.4"

from redteam_arena.agents.agent import Agent
from redteam_arena.agents.blue_agent import BlueAgent
from redteam_arena.agents.claude_adapter import ClaudeAdapter, validate_api_key
from redteam_arena.agents.provider import Provider
from redteam_arena.agents.provider_registry import (
    create_provider,
    detect_provider,
    validate_provider,
)
from redteam_arena.agents.red_agent import RedAgent
from redteam_arena.agents.response_parser import parse_findings, parse_mitigations
from redteam_arena.core.battle_engine import BattleEngine, BattleEngineOptions
from redteam_arena.core.battle_store import BattleStore
from redteam_arena.core.config import load_config, merge_config
from redteam_arena.core.event_system import BattleEventSystem
from redteam_arena.core.file_reader import format_files_for_prompt, has_source_files, read_codebase
from redteam_arena.reports.battle_report import generate_report, write_report
from redteam_arena.reports.html_reporter import generate_html_report
from redteam_arena.reports.sarif_reporter import generate_json_report, generate_sarif_report
from redteam_arena.scenarios.scenario import list_scenarios, load_scenario
from redteam_arena.types import (
    AgentContext,
    Battle,
    BattleConfig,
    BattleEvent,
    BattleStatus,
    BattleSummary,
    FileEntry,
    Finding,
    Message,
    Mitigation,
    ProviderId,
    ReportFormat,
    Result,
    Round,
    Scenario,
    Severity,
    StreamOptions,
)

__all__ = [
    "__version__",
    # Engine
    "BattleEngine",
    "BattleEngineOptions",
    "BattleEventSystem",
    "BattleStore",
    # File reading
    "read_codebase",
    "format_files_for_prompt",
    "has_source_files",
    # Providers
    "ClaudeAdapter",
    "validate_api_key",
    "create_provider",
    "detect_provider",
    "validate_provider",
    # Agents
    "RedAgent",
    "BlueAgent",
    "Agent",
    "Provider",
    # Parsing
    "parse_findings",
    "parse_mitigations",
    # Scenarios
    "load_scenario",
    "list_scenarios",
    # Reports
    "generate_report",
    "write_report",
    "generate_sarif_report",
    "generate_json_report",
    "generate_html_report",
    # Config
    "load_config",
    "merge_config",
    # Types
    "Battle",
    "BattleConfig",
    "BattleEvent",
    "BattleStatus",
    "BattleSummary",
    "Finding",
    "Mitigation",
    "ProviderId",
    "ReportFormat",
    "Round",
    "Scenario",
    "Severity",
    "FileEntry",
    "AgentContext",
    "StreamOptions",
    "Message",
    "Result",
]
