"""
Battle history storage -- persists battle records to JSON files.
Stores data in ~/.redteam-arena/history/battles.json.
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from redteam_arena.types import Battle, BattleStatus, Finding


@dataclass
class BattleRecord:
    id: str
    scenario: str
    target_dir: str
    status: BattleStatus
    total_findings: int
    findings_by_severity: dict[str, int]
    total_mitigations: int
    mitigation_coverage: float
    rounds: int
    started_at: str
    ended_at: str | None = None
    commit_hash: str | None = None
    branch: str | None = None
    provider: str | None = None
    model: str | None = None
    duration: int | None = None


@dataclass
class BattleQuery:
    scenario: str | None = None
    target_dir: str | None = None
    since: str | None = None
    limit: int = 50
    status: BattleStatus | None = None


@dataclass
class BattleTrend:
    period: str
    total_battles: int
    total_findings: int
    avg_coverage: float
    by_severity: dict[str, int]


class BattleStore:
    def __init__(self) -> None:
        self._store_dir = os.path.join(
            Path.home(), ".redteam-arena", "history"
        )

    async def save(self, battle: Battle) -> BattleRecord:
        """Convert a Battle to a BattleRecord and persist it."""
        self._ensure_dir()

        all_findings = [f for r in battle.rounds for f in r.findings]
        all_mitigations = [m for r in battle.rounds for m in r.mitigations]

        findings_by_severity: dict[str, int] = {
            "critical": 0, "high": 0, "medium": 0, "low": 0,
        }
        for f in all_findings:
            findings_by_severity[f.severity] += 1

        mitigation_coverage = (
            len(all_mitigations) / len(all_findings)
            if all_findings
            else 1.0
        )

        start_ms = int(battle.started_at.timestamp() * 1000)
        end_ms = (
            int(battle.ended_at.timestamp() * 1000)
            if battle.ended_at
            else None
        )

        git_info = await self._get_git_info(battle.config.target_dir)

        record = BattleRecord(
            id=battle.id,
            scenario=battle.config.scenario.name,
            target_dir=battle.config.target_dir,
            status=battle.status,
            total_findings=len(all_findings),
            findings_by_severity=findings_by_severity,
            total_mitigations=len(all_mitigations),
            mitigation_coverage=mitigation_coverage,
            rounds=len(battle.rounds),
            started_at=battle.started_at.isoformat(),
            ended_at=battle.ended_at.isoformat() if battle.ended_at else None,
            commit_hash=git_info.get("commit_hash"),
            branch=git_info.get("branch"),
            duration=(end_ms - start_ms) if end_ms is not None else None,
        )

        records = self._read_index()
        records.append(record)
        self._write_index(records)

        # Persist per-battle findings for regression analysis
        self._save_battle_findings(battle.id, all_findings)

        return record

    async def query(self, query: BattleQuery | None = None) -> list[BattleRecord]:
        """Query stored battle records with optional filters."""
        records = self._read_index()
        limit = query.limit if query else 50

        filtered = records

        if query:
            if query.scenario:
                filtered = [r for r in filtered if r.scenario == query.scenario]
            if query.target_dir:
                filtered = [r for r in filtered if r.target_dir == query.target_dir]
            if query.status:
                filtered = [r for r in filtered if r.status == query.status]
            if query.since:
                since_dt = datetime.fromisoformat(query.since)
                filtered = [
                    r for r in filtered
                    if datetime.fromisoformat(r.started_at) >= since_dt
                ]

        # Most recent first
        filtered.sort(
            key=lambda r: r.started_at,
            reverse=True,
        )

        return filtered[:limit]

    async def get(self, battle_id: str) -> BattleRecord | None:
        """Get a single battle record by ID."""
        records = self._read_index()
        return next((r for r in records if r.id == battle_id), None)

    async def get_trends(
        self,
        target_dir: str,
        days: int = 30,
    ) -> list[BattleTrend]:
        """Aggregate battle data by day for a given target directory."""
        cutoff = datetime.now()
        cutoff = cutoff.replace(
            day=max(1, cutoff.day - days) if cutoff.day > days else 1
        )

        records = self._read_index()
        relevant = [
            r for r in records
            if r.target_dir == target_dir
            and datetime.fromisoformat(r.started_at) >= cutoff
        ]

        # Group by YYYY-MM-DD
        groups: dict[str, list[BattleRecord]] = {}
        for record in relevant:
            period = record.started_at[:10]
            groups.setdefault(period, []).append(record)

        trends: list[BattleTrend] = []
        for period, group in sorted(groups.items()):
            by_severity: dict[str, int] = {
                "critical": 0, "high": 0, "medium": 0, "low": 0,
            }
            total_findings = 0
            total_coverage = 0.0

            for record in group:
                total_findings += record.total_findings
                total_coverage += record.mitigation_coverage
                for sev, count in record.findings_by_severity.items():
                    by_severity[sev] = by_severity.get(sev, 0) + count

            trends.append(
                BattleTrend(
                    period=period,
                    total_battles=len(group),
                    total_findings=total_findings,
                    avg_coverage=(
                        total_coverage / len(group) if group else 0
                    ),
                    by_severity=by_severity,
                )
            )

        return trends

    async def get_regression(
        self,
        target_dir: str,
    ) -> dict[str, list[dict]] | None:
        """Compare the last two battles for a target directory."""
        records = self._read_index()
        matching = sorted(
            [r for r in records if r.target_dir == target_dir],
            key=lambda r: r.started_at,
            reverse=True,
        )

        if len(matching) < 2:
            return None

        latest_findings = self._read_battle_findings(matching[0].id)
        previous_findings = self._read_battle_findings(matching[1].id)

        if latest_findings is None or previous_findings is None:
            return None

        previous_keys = {
            f"{f['file_path']}::{f['description']}" for f in previous_findings
        }
        latest_keys = {
            f"{f['file_path']}::{f['description']}" for f in latest_findings
        }

        new_findings = [
            f for f in latest_findings
            if f"{f['file_path']}::{f['description']}" not in previous_keys
        ]
        resolved_findings = [
            f for f in previous_findings
            if f"{f['file_path']}::{f['description']}" not in latest_keys
        ]

        return {
            "new_findings": new_findings,
            "resolved_findings": resolved_findings,
        }

    async def clear(self) -> None:
        """Remove all stored battle data."""
        self._ensure_dir()
        self._write_index([])

        # Remove detail files
        try:
            for filename in os.listdir(self._store_dir):
                if filename.startswith("battle-") and filename.endswith(".json"):
                    os.unlink(os.path.join(self._store_dir, filename))
        except OSError:
            pass

    # --- Private helpers ---

    def _get_store_path(self) -> str:
        return os.path.join(self._store_dir, "battles.json")

    def _ensure_dir(self) -> None:
        os.makedirs(self._store_dir, exist_ok=True)

    def _read_index(self) -> list[BattleRecord]:
        try:
            with open(self._get_store_path(), encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                return []
            return [BattleRecord(**item) for item in data]
        except (OSError, json.JSONDecodeError, TypeError):
            return []

    def _write_index(self, records: list[BattleRecord]) -> None:
        self._ensure_dir()
        with open(self._get_store_path(), "w", encoding="utf-8") as f:
            json.dump([asdict(r) for r in records], f, indent=2)

    def _read_battle_findings(self, battle_id: str) -> list[dict] | None:
        detail_path = os.path.join(self._store_dir, f"battle-{battle_id}.json")
        try:
            with open(detail_path, encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict) and isinstance(data.get("findings"), list):
                return data["findings"]
            return None
        except (OSError, json.JSONDecodeError):
            return None

    def _save_battle_findings(
        self,
        battle_id: str,
        findings: list[Finding],
    ) -> None:
        self._ensure_dir()
        detail_path = os.path.join(self._store_dir, f"battle-{battle_id}.json")
        findings_data = [
            {
                "id": f.id,
                "round_number": f.round_number,
                "file_path": f.file_path,
                "line_reference": f.line_reference,
                "description": f.description,
                "attack_vector": f.attack_vector,
                "severity": f.severity,
                "code_snippet": f.code_snippet,
            }
            for f in findings
        ]
        with open(detail_path, "w", encoding="utf-8") as f:
            json.dump({"findings": findings_data}, f, indent=2)

    async def _get_git_info(self, directory: str) -> dict[str, str]:
        result: dict[str, str] = {}
        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "rev-parse", "HEAD",
                cwd=directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                result["commit_hash"] = stdout.decode().strip()
        except Exception:
            pass

        try:
            proc = await asyncio.create_subprocess_exec(
                "git", "rev-parse", "--abbrev-ref", "HEAD",
                cwd=directory,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await proc.communicate()
            if proc.returncode == 0:
                result["branch"] = stdout.decode().strip()
        except Exception:
            pass

        return result
