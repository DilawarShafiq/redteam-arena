"""
Team collaboration -- finding assignments, comments, and webhook notifications.
Stores team data in ~/.redteam-arena/team/.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal

AssignmentStatus = Literal[
    "open", "acknowledged", "in-progress", "fixed", "wont-fix", "false-positive"
]


@dataclass
class FindingAssignment:
    finding_id: str
    assignee: str
    status: AssignmentStatus = "open"
    notes: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass
class FindingComment:
    id: str
    finding_id: str
    author: str
    text: str
    created_at: str = ""


@dataclass
class WebhookConfig:
    url: str
    events: list[str] = field(default_factory=lambda: ["battle-end"])
    headers: dict[str, str] = field(default_factory=dict)
    enabled: bool = True


@dataclass
class TeamConfig:
    assignments: list[FindingAssignment] = field(default_factory=list)
    comments: list[FindingComment] = field(default_factory=list)
    webhooks: list[WebhookConfig] = field(default_factory=list)


class TeamManager:
    def __init__(self) -> None:
        self._store_dir = os.path.join(
            Path.home(), ".redteam-arena", "team"
        )
        self._config: TeamConfig | None = None

    def _ensure_dir(self) -> None:
        os.makedirs(self._store_dir, exist_ok=True)

    def _get_config_path(self) -> str:
        return os.path.join(self._store_dir, "team.json")

    def _load_config(self) -> TeamConfig:
        if self._config is not None:
            return self._config

        try:
            with open(self._get_config_path(), encoding="utf-8") as f:
                data = json.load(f)

            self._config = TeamConfig(
                assignments=[
                    FindingAssignment(**a) for a in data.get("assignments", [])
                ],
                comments=[
                    FindingComment(**c) for c in data.get("comments", [])
                ],
                webhooks=[
                    WebhookConfig(**w) for w in data.get("webhooks", [])
                ],
            )
        except (OSError, json.JSONDecodeError, TypeError):
            self._config = TeamConfig()

        return self._config

    def _save_config(self) -> None:
        self._ensure_dir()
        config = self._load_config()
        with open(self._get_config_path(), "w", encoding="utf-8") as f:
            json.dump(asdict(config), f, indent=2)

    # --- Assignments ---

    async def assign_finding(
        self,
        finding_id: str,
        assignee: str,
        notes: str = "",
    ) -> FindingAssignment:
        """Assign a finding to a team member."""
        config = self._load_config()
        now = datetime.now().isoformat()

        # Check for existing assignment
        existing = next(
            (a for a in config.assignments if a.finding_id == finding_id),
            None,
        )

        if existing:
            existing.assignee = assignee
            existing.notes = notes
            existing.updated_at = now
            self._save_config()
            return existing

        assignment = FindingAssignment(
            finding_id=finding_id,
            assignee=assignee,
            status="open",
            notes=notes,
            created_at=now,
            updated_at=now,
        )
        config.assignments.append(assignment)
        self._save_config()
        return assignment

    async def update_status(
        self,
        finding_id: str,
        status: AssignmentStatus,
    ) -> FindingAssignment | None:
        """Update the status of a finding assignment."""
        config = self._load_config()
        assignment = next(
            (a for a in config.assignments if a.finding_id == finding_id),
            None,
        )
        if not assignment:
            return None

        assignment.status = status
        assignment.updated_at = datetime.now().isoformat()
        self._save_config()
        return assignment

    async def get_assignments(
        self,
        *,
        assignee: str = "",
        status: str = "",
    ) -> list[FindingAssignment]:
        """Get assignments with optional filtering."""
        config = self._load_config()
        result = config.assignments

        if assignee:
            result = [a for a in result if a.assignee == assignee]
        if status:
            result = [a for a in result if a.status == status]

        return result

    # --- Comments ---

    async def add_comment(
        self,
        finding_id: str,
        author: str,
        text: str,
    ) -> FindingComment:
        """Add a comment to a finding."""
        import secrets

        config = self._load_config()
        comment = FindingComment(
            id=secrets.token_urlsafe(6),
            finding_id=finding_id,
            author=author,
            text=text,
            created_at=datetime.now().isoformat(),
        )
        config.comments.append(comment)
        self._save_config()
        return comment

    async def get_comments(self, finding_id: str) -> list[FindingComment]:
        """Get all comments for a finding."""
        config = self._load_config()
        return [c for c in config.comments if c.finding_id == finding_id]

    # --- Webhooks ---

    async def add_webhook(self, webhook: WebhookConfig) -> None:
        """Add a webhook configuration."""
        config = self._load_config()
        config.webhooks.append(webhook)
        self._save_config()

    async def remove_webhook(self, url: str) -> bool:
        """Remove a webhook by URL."""
        config = self._load_config()
        original_count = len(config.webhooks)
        config.webhooks = [w for w in config.webhooks if w.url != url]
        if len(config.webhooks) < original_count:
            self._save_config()
            return True
        return False

    async def fire_webhooks(self, event_type: str, payload: dict) -> list[dict]:
        """Fire all matching webhooks. Returns results."""
        config = self._load_config()
        results: list[dict] = []

        matching = [
            w for w in config.webhooks
            if w.enabled and event_type in w.events
        ]

        if not matching:
            return results

        try:
            import httpx
        except ImportError:
            return [{"url": w.url, "status": "error", "message": "httpx not installed"} for w in matching]

        async with httpx.AsyncClient(timeout=10.0) as client:
            for webhook in matching:
                try:
                    headers = {**webhook.headers, "Content-Type": "application/json"}
                    resp = await client.post(
                        webhook.url,
                        json={"event": event_type, **payload},
                        headers=headers,
                    )
                    results.append({
                        "url": webhook.url,
                        "status": "ok",
                        "code": resp.status_code,
                    })
                except Exception as exc:
                    results.append({
                        "url": webhook.url,
                        "status": "error",
                        "message": str(exc),
                    })

        return results

    async def get_webhooks(self) -> list[WebhookConfig]:
        """Get all webhook configurations."""
        config = self._load_config()
        return config.webhooks
