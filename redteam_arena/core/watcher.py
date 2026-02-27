"""
Watch mode -- monitors source files for changes and triggers re-scans.
Uses watchdog for cross-platform recursive watching.
"""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Callable
from typing import Any

from rich.console import Console

from redteam_arena.types import ProviderId, Scenario

console = Console()

WATCHED_EXTENSIONS = {
    ".ts", ".js", ".tsx", ".jsx",
    ".py",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".c", ".cpp", ".h",
    ".cs",
    ".swift",
    ".kt",
}

IGNORED_DIRS = {
    "node_modules", ".git", "dist", "build", "coverage",
    "__pycache__", ".venv", "venv",
}

DEBOUNCE_MS = 500


class WatchMode:
    def __init__(
        self,
        target_dir: str,
        scenario: Scenario,
        rounds: int,
        provider_id: ProviderId,
        *,
        model: str = "",
        format: str = "markdown",
        output_path: str = "",
        on_change: Callable[[list[str]], None] | None = None,
    ) -> None:
        self._target_dir = target_dir
        self._scenario = scenario
        self._rounds = rounds
        self._provider_id = provider_id
        self._model = model
        self._format = format
        self._output_path = output_path
        self._on_change = on_change

        self._observer: Any = None
        self._changed_files: set[str] = set()
        self._debounce_timer: threading.Timer | None = None
        self._ignore_patterns: list[str] = []
        self.running = False

    def start(self) -> None:
        """Start watching for file changes."""
        if self.running:
            console.print("  Watch mode is already running.", style="yellow")
            return

        self.running = True
        self._load_ignore_patterns()

        console.print()
        console.print(
            f"  Watching {self._target_dir} for changes...",
            style="bold cyan",
        )
        console.print(
            f"  Scenario: {self._scenario.name} | Rounds: {self._rounds} | Provider: {self._provider_id}",
            style="dim",
        )
        console.print("  Press Ctrl+C to stop watching.", style="dim")
        console.print()

        try:
            from watchdog.observers import Observer

            handler = _WatchdogHandler(self)
            self._observer = Observer()
            self._observer.schedule(handler, self._target_dir, recursive=True)
            self._observer.start()
            console.print("  (using watchdog for cross-platform watching)", style="dim")
        except ImportError:
            console.print(
                "  Warning: watchdog not installed. Install with: pip install watchdog",
                style="yellow",
            )
            self.running = False

    def stop(self) -> None:
        """Stop watching."""
        if not self.running:
            return

        if self._debounce_timer:
            self._debounce_timer.cancel()
            self._debounce_timer = None

        if self._observer is not None:
            self._observer.stop()
            self._observer.join()
            self._observer = None

        self._changed_files.clear()
        self.running = False

        console.print()
        console.print("  Watch mode stopped.", style="cyan")

    def on_file_change(self, file_path: str) -> None:
        """Handle a file change event."""
        normalized = file_path.replace("\\", "/")

        # Check ignored directories
        segments = normalized.split("/")
        for segment in segments:
            if segment in IGNORED_DIRS:
                return

        # Check ignore patterns
        rel = os.path.relpath(file_path, self._target_dir).replace("\\", "/")
        if self._matches_ignore_pattern(rel):
            return

        # Check extension
        ext = os.path.splitext(normalized)[1].lower()
        if ext not in WATCHED_EXTENSIONS:
            return

        self._changed_files.add(rel)
        console.print(f"  Changed: {rel}", style="dim")

        # Debounce
        if self._debounce_timer:
            self._debounce_timer.cancel()

        self._debounce_timer = threading.Timer(
            DEBOUNCE_MS / 1000.0, self._flush_changes
        )
        self._debounce_timer.start()

    def _flush_changes(self) -> None:
        """Process accumulated file changes."""
        if not self._changed_files:
            return

        files = list(self._changed_files)
        self._changed_files.clear()
        self._debounce_timer = None

        timestamp = time.strftime("%H:%M:%S")
        console.print()
        console.print(
            f"  [{timestamp}] Re-scanning {len(files)} changed file(s)...",
            style="bold cyan",
        )
        for f in files:
            console.print(f"    - {f}", style="dim")
        console.print()

        if self._on_change:
            self._on_change(files)

    def _load_ignore_patterns(self) -> None:
        """Load .redteamignore patterns."""
        ignore_path = os.path.join(self._target_dir, ".redteamignore")
        try:
            with open(ignore_path, encoding="utf-8") as f:
                self._ignore_patterns = [
                    line.strip()
                    for line in f.readlines()
                    if line.strip() and not line.strip().startswith("#")
                ]
        except OSError:
            self._ignore_patterns = []

    def _matches_ignore_pattern(self, relative_path: str) -> bool:
        """Check if a path matches any .redteamignore patterns."""
        import fnmatch

        for pattern in self._ignore_patterns:
            if pattern.endswith("/"):
                if relative_path.startswith(pattern) or f"/{pattern}" in relative_path:
                    return True
            elif "*" in pattern or "?" in pattern:
                if fnmatch.fnmatch(relative_path, pattern):
                    return True
            else:
                if relative_path == pattern or relative_path.endswith(f"/{pattern}"):
                    return True
        return False


class _WatchdogHandler:
    """Adapter for watchdog FileSystemEventHandler."""

    def __init__(self, watcher: WatchMode) -> None:
        self._watcher = watcher

    def dispatch(self, event: object) -> None:
        """Handle watchdog events."""
        if hasattr(event, "is_directory") and getattr(event, "is_directory"):
            return
        src_path = getattr(event, "src_path", None)
        if src_path and isinstance(src_path, str):
            event_type = getattr(event, "event_type", "")
            if event_type in ("created", "modified"):
                self._watcher.on_file_change(src_path)
