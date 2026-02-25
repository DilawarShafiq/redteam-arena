"""
Core type definitions for RedTeam Arena.
All entities, events, and configuration types.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Generic, Literal, TypeVar, Union

# --- Severity ---

Severity = Literal["critical", "high", "medium", "low"]

# --- Confidence ---

Confidence = Literal["high", "medium", "low"]

# --- Finding ---


@dataclass
class Finding:
    id: str
    round_number: int
    file_path: str
    line_reference: str
    description: str
    attack_vector: str
    severity: Severity
    code_snippet: str | None = None


# --- Mitigation ---


@dataclass
class Mitigation:
    id: str
    finding_id: str
    round_number: int
    acknowledgment: str
    proposed_fix: str
    confidence: Confidence


# --- Round ---


@dataclass
class Round:
    number: int
    findings: list[Finding]
    mitigations: list[Mitigation]
    red_raw_output: str
    blue_raw_output: str


# --- Scenario ---


@dataclass
class Scenario:
    name: str
    description: str
    focus_areas: list[str]
    severity_guidance: str
    red_guidance: str
    blue_guidance: str
    is_meta: bool = False
    sub_scenarios: list[str] = field(default_factory=list)


# --- File Entry ---


@dataclass
class FileEntry:
    path: str
    content: str


# --- Agent Context ---


@dataclass
class AgentContext:
    scenario: Scenario
    files: list[FileEntry]
    previous_findings: list[Finding]
    previous_mitigations: list[Mitigation]
    round_number: int
    role: Literal["red", "blue"]


# --- Stream Options ---


@dataclass
class StreamOptions:
    model: str
    max_tokens: int
    system_prompt: str


# --- Messages ---


@dataclass
class Message:
    role: Literal["user", "assistant"]
    content: str


# --- Battle Status ---

BattleStatus = Literal["pending", "running", "completed", "interrupted", "error"]


# --- Battle Config ---


@dataclass
class BattleConfig:
    target_dir: str
    scenario: Scenario
    rounds: int


# --- Battle Event (discriminated union via type field) ---


@dataclass
class BattleStartEvent:
    type: Literal["battle-start"] = "battle-start"
    timestamp: datetime = field(default_factory=datetime.now)
    battle_id: str = ""
    scenario: str = ""
    target_dir: str = ""


@dataclass
class RoundStartEvent:
    type: Literal["round-start"] = "round-start"
    timestamp: datetime = field(default_factory=datetime.now)
    round_number: int = 0


@dataclass
class AttackEvent:
    type: Literal["attack"] = "attack"
    timestamp: datetime = field(default_factory=datetime.now)
    round_number: int = 0
    findings: list[Finding] = field(default_factory=list)


@dataclass
class DefendEvent:
    type: Literal["defend"] = "defend"
    timestamp: datetime = field(default_factory=datetime.now)
    round_number: int = 0
    mitigations: list[Mitigation] = field(default_factory=list)


@dataclass
class RoundEndEvent:
    type: Literal["round-end"] = "round-end"
    timestamp: datetime = field(default_factory=datetime.now)
    round_number: int = 0
    finding_count: int = 0
    mitigation_count: int = 0


@dataclass
class BattleEndEvent:
    type: Literal["battle-end"] = "battle-end"
    timestamp: datetime = field(default_factory=datetime.now)
    battle_id: str = ""
    status: BattleStatus = "completed"
    summary: BattleSummary | None = None


@dataclass
class ErrorEvent:
    type: Literal["error"] = "error"
    timestamp: datetime = field(default_factory=datetime.now)
    message: str = ""
    phase: str = ""


BattleEvent = Union[
    BattleStartEvent,
    RoundStartEvent,
    AttackEvent,
    DefendEvent,
    RoundEndEvent,
    BattleEndEvent,
    ErrorEvent,
]


# --- Battle Summary ---


@dataclass
class BattleSummary:
    total_rounds: int
    total_findings: int
    findings_by_severity: dict[str, int]
    total_mitigations: int
    mitigation_coverage: float


# --- Battle ---


@dataclass
class Battle:
    id: str
    config: BattleConfig
    rounds: list[Round]
    events: list[BattleEvent]
    status: BattleStatus
    started_at: datetime
    ended_at: datetime | None = None


# --- Result type for error handling ---

T = TypeVar("T")
E = TypeVar("E", bound=Exception)


@dataclass
class Ok(Generic[T]):
    value: T
    ok: Literal[True] = True


@dataclass
class Err(Generic[E]):
    error: E
    ok: Literal[False] = False


Result = Union[Ok[T], Err[E]]
