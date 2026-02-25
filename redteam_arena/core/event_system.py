"""
Typed event system for battle state tracking.
Provides typed BattleEvent support and in-memory log.
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from typing import Any

from redteam_arena.types import BattleEvent


class BattleEventSystem:
    def __init__(self) -> None:
        self._log: list[BattleEvent] = []
        self._handlers: dict[str, list[Callable[..., Any]]] = defaultdict(list)

    def emit(self, event: BattleEvent) -> None:
        """Emit an event: log it and notify handlers."""
        self._log.append(event)
        event_type = event.type
        for handler in self._handlers.get(event_type, []):
            handler(event)

    def on(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Register a handler for a specific event type."""
        self._handlers[event_type].append(handler)

    def off(self, event_type: str, handler: Callable[..., Any]) -> None:
        """Remove a handler for a specific event type."""
        handlers = self._handlers.get(event_type, [])
        if handler in handlers:
            handlers.remove(handler)

    def get_log(self) -> list[BattleEvent]:
        """Return the full event log."""
        return self._log

    def get_events_by_type(self, event_type: str) -> list[BattleEvent]:
        """Return only events matching the requested type."""
        return [e for e in self._log if e.type == event_type]

    def clear(self) -> None:
        """Remove all events from the log and all listeners."""
        self._log = []
        self._handlers.clear()
