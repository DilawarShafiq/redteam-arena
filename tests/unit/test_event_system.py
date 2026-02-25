"""Tests for redteam_arena.core.event_system."""

from __future__ import annotations

from datetime import datetime

import pytest

from redteam_arena.core.event_system import BattleEventSystem
from redteam_arena.types import (
    AttackEvent,
    BattleEndEvent,
    BattleStartEvent,
    BattleSummary,
    DefendEvent,
    ErrorEvent,
    Finding,
    Mitigation,
    RoundEndEvent,
    RoundStartEvent,
)


def make_finding() -> Finding:
    return Finding(
        id="abc12345",
        round_number=1,
        file_path="src/db.ts",
        line_reference="42",
        description="SQL injection in query builder",
        attack_vector="User-controlled input concatenated into raw SQL",
        severity="high",
    )


def make_mitigation() -> Mitigation:
    return Mitigation(
        id="mit12345",
        finding_id="abc12345",
        round_number=1,
        acknowledgment="Confirmed SQL injection risk",
        proposed_fix="Use parameterized queries",
        confidence="high",
    )


class TestEmit:
    def test_adds_a_single_event_to_the_log(self) -> None:
        event_system = BattleEventSystem()
        event = BattleStartEvent(
            timestamp=datetime.now(),
            battle_id="battle-1",
            scenario="sql-injection",
            target_dir="/tmp/app",
        )

        event_system.emit(event)

        assert len(event_system.get_log()) == 1
        assert event_system.get_log()[0] is event

    def test_adds_multiple_events_in_order(self) -> None:
        event_system = BattleEventSystem()
        event1 = BattleStartEvent(
            timestamp=datetime.now(),
            battle_id="battle-1",
            scenario="sql-injection",
            target_dir="/tmp/app",
        )
        event2 = RoundStartEvent(timestamp=datetime.now(), round_number=1)
        event3 = RoundEndEvent(
            timestamp=datetime.now(),
            round_number=1,
            finding_count=2,
            mitigation_count=2,
        )

        event_system.emit(event1)
        event_system.emit(event2)
        event_system.emit(event3)

        log = event_system.get_log()
        assert len(log) == 3
        assert log[0] is event1
        assert log[1] is event2
        assert log[2] is event3


class TestOn:
    def test_handler_called_with_correct_event(self) -> None:
        event_system = BattleEventSystem()
        received: list = []

        event_system.on("attack", lambda e: received.append(e))

        attack_event = AttackEvent(
            timestamp=datetime.now(),
            round_number=1,
            findings=[make_finding()],
        )

        event_system.emit(attack_event)

        assert len(received) == 1
        assert received[0] is attack_event

    def test_handler_not_called_for_other_event_types(self) -> None:
        event_system = BattleEventSystem()
        received: list = []

        event_system.on("attack", lambda e: received.append(e))

        unrelated_event = RoundStartEvent(timestamp=datetime.now(), round_number=1)

        event_system.emit(unrelated_event)

        assert len(received) == 0

    def test_multiple_handlers_for_same_type(self) -> None:
        event_system = BattleEventSystem()
        calls: list[int] = []

        event_system.on("defend", lambda _: calls.append(1))
        event_system.on("defend", lambda _: calls.append(2))

        defend_event = DefendEvent(
            timestamp=datetime.now(),
            round_number=1,
            mitigations=[make_mitigation()],
        )

        event_system.emit(defend_event)

        assert calls == [1, 2]

    def test_handler_receives_typed_event_data(self) -> None:
        event_system = BattleEventSystem()
        captured: list[int] = []

        event_system.on("round-end", lambda e: captured.append(e.finding_count))

        round_end_event = RoundEndEvent(
            timestamp=datetime.now(),
            round_number=1,
            finding_count=5,
            mitigation_count=4,
        )

        event_system.emit(round_end_event)

        assert captured == [5]


class TestGetLog:
    def test_returns_empty_before_any_events(self) -> None:
        event_system = BattleEventSystem()
        assert len(event_system.get_log()) == 0

    def test_returns_all_events_in_emission_order(self) -> None:
        event_system = BattleEventSystem()
        events = [
            BattleStartEvent(
                timestamp=datetime.now(),
                battle_id="b1",
                scenario="xss",
                target_dir="/app",
            ),
            RoundStartEvent(timestamp=datetime.now(), round_number=1),
            AttackEvent(timestamp=datetime.now(), round_number=1, findings=[]),
            DefendEvent(timestamp=datetime.now(), round_number=1, mitigations=[]),
            RoundEndEvent(
                timestamp=datetime.now(),
                round_number=1,
                finding_count=0,
                mitigation_count=0,
            ),
        ]

        for e in events:
            event_system.emit(e)

        log = event_system.get_log()
        assert len(log) == len(events)
        for i in range(len(events)):
            assert log[i] is events[i]

    def test_returns_error_events_correctly(self) -> None:
        event_system = BattleEventSystem()
        event = ErrorEvent(
            timestamp=datetime.now(),
            message="Something went wrong",
            phase="attack",
        )
        # Register handler to avoid any issues
        event_system.on("error", lambda _: None)

        event_system.emit(event)

        log = event_system.get_log()
        assert len(log) == 1
        assert log[0].type == "error"


class TestGetEventsByType:
    def test_returns_only_matching_events(self) -> None:
        event_system = BattleEventSystem()
        attack_event = AttackEvent(
            timestamp=datetime.now(),
            round_number=1,
            findings=[make_finding()],
        )
        round_start_event = RoundStartEvent(timestamp=datetime.now(), round_number=1)

        event_system.emit(attack_event)
        event_system.emit(round_start_event)
        event_system.emit(attack_event)

        attacks = event_system.get_events_by_type("attack")
        assert len(attacks) == 2
        for a in attacks:
            assert a.type == "attack"

    def test_returns_empty_when_no_events_of_type(self) -> None:
        event_system = BattleEventSystem()
        event = RoundStartEvent(timestamp=datetime.now(), round_number=1)
        event_system.emit(event)

        attacks = event_system.get_events_by_type("attack")
        assert len(attacks) == 0

    def test_filters_correctly_across_mixed_types(self) -> None:
        event_system = BattleEventSystem()
        e1 = BattleStartEvent(
            timestamp=datetime.now(),
            battle_id="b1",
            scenario="s",
            target_dir="/d",
        )
        e2 = RoundStartEvent(timestamp=datetime.now(), round_number=1)
        e3 = RoundStartEvent(timestamp=datetime.now(), round_number=2)
        e4 = BattleEndEvent(
            timestamp=datetime.now(),
            battle_id="b1",
            status="completed",
            summary=BattleSummary(
                total_rounds=2,
                total_findings=0,
                findings_by_severity={"critical": 0, "high": 0, "medium": 0, "low": 0},
                total_mitigations=0,
                mitigation_coverage=100,
            ),
        )

        event_system.emit(e1)
        event_system.emit(e2)
        event_system.emit(e3)
        event_system.emit(e4)

        round_starts = event_system.get_events_by_type("round-start")
        assert len(round_starts) == 2
        assert round_starts[0].round_number == 1
        assert round_starts[1].round_number == 2


class TestClear:
    def test_removes_all_events_from_log(self) -> None:
        event_system = BattleEventSystem()
        event_system.emit(RoundStartEvent(timestamp=datetime.now(), round_number=1))
        event_system.emit(RoundStartEvent(timestamp=datetime.now(), round_number=2))

        assert len(event_system.get_log()) == 2

        event_system.clear()

        assert len(event_system.get_log()) == 0

    def test_removes_listeners_so_handlers_not_called(self) -> None:
        event_system = BattleEventSystem()
        call_count = [0]
        event_system.on("round-start", lambda _: call_count.__setitem__(0, call_count[0] + 1))

        event_system.emit(RoundStartEvent(timestamp=datetime.now(), round_number=1))
        assert call_count[0] == 1

        event_system.clear()

        event_system.emit(RoundStartEvent(timestamp=datetime.now(), round_number=2))
        # Log has the event but the old handler is gone
        assert call_count[0] == 1

    def test_allows_new_events_after_clearing(self) -> None:
        event_system = BattleEventSystem()
        event_system.emit(RoundStartEvent(timestamp=datetime.now(), round_number=1))
        event_system.clear()

        new_event = RoundStartEvent(timestamp=datetime.now(), round_number=2)
        event_system.emit(new_event)

        log = event_system.get_log()
        assert len(log) == 1
        assert log[0] is new_event
