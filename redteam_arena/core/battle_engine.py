"""
Battle engine -- runs the Red vs Blue battle loop.
Alternates agent turns, tracks state, emits events.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime

from redteam_arena.agents.agent import Agent
from redteam_arena.agents.response_parser import parse_findings, parse_mitigations
from redteam_arena.core.event_system import BattleEventSystem
from redteam_arena.core.file_reader import has_source_files, read_codebase
from redteam_arena.display import (
    display_agent_done,
    display_blue_chunk,
    display_blue_header,
    display_finding,
    display_mitigation,
    display_red_chunk,
    display_red_header,
    display_round_end,
    display_round_start,
)
from redteam_arena.types import (
    AgentContext,
    AttackEvent,
    Battle,
    BattleConfig,
    BattleEndEvent,
    BattleStartEvent,
    BattleSummary,
    DefendEvent,
    ErrorEvent,
    FileEntry,
    Finding,
    Mitigation,
    Round,
    RoundEndEvent,
    RoundStartEvent,
)


@dataclass
class BattleEngineOptions:
    red_agent: Agent
    blue_agent: Agent
    config: BattleConfig
    on_interrupt: object | None = None
    override_files: list[FileEntry] | None = None


class BattleEngine:
    def __init__(self, options: BattleEngineOptions) -> None:
        self._red_agent = options.red_agent
        self._blue_agent = options.blue_agent
        self._config = options.config
        self._events = BattleEventSystem()
        self._interrupted = False
        self._override_files = options.override_files

        self._battle = Battle(
            id=uuid.uuid4().hex[:8],
            config=self._config,
            rounds=[],
            events=[],
            status="pending",
            started_at=datetime.now(),
        )

    def interrupt(self) -> None:
        self._interrupted = True

    def get_battle(self) -> Battle:
        return Battle(
            id=self._battle.id,
            config=self._battle.config,
            rounds=list(self._battle.rounds),
            events=list(self._events.get_log()),
            status=self._battle.status,
            started_at=self._battle.started_at,
            ended_at=self._battle.ended_at,
        )

    async def run(self) -> Battle:
        """Run the full battle loop."""
        # Use override_files (e.g. from --diff) or read codebase
        if self._override_files is not None:
            files = self._override_files
        else:
            code_result = await read_codebase(self._config.target_dir)
            if not code_result.ok:
                raise RuntimeError(code_result.error.args[0] if code_result.error.args else str(code_result.error))
            files = code_result.value

        if not has_source_files(files):
            raise RuntimeError(f"No source files found in {self._config.target_dir}")

        # Start battle
        self._battle.status = "running"
        self._events.emit(
            BattleStartEvent(
                timestamp=datetime.now(),
                battle_id=self._battle.id,
                scenario=self._config.scenario.name,
                target_dir=self._config.target_dir,
            )
        )

        all_findings: list[Finding] = []
        all_mitigations: list[Mitigation] = []

        try:
            for round_num in range(1, self._config.rounds + 1):
                if self._interrupted:
                    break

                round_result = await self._run_round(
                    round_num, files, all_findings, all_mitigations
                )
                self._battle.rounds.append(round_result)
                all_findings.extend(round_result.findings)
                all_mitigations.extend(round_result.mitigations)

            if self._interrupted:
                self._battle.status = "interrupted"
            else:
                self._battle.status = "completed"
        except Exception as err:
            self._battle.status = "error"
            self._events.emit(
                ErrorEvent(
                    timestamp=datetime.now(),
                    message=str(err),
                    phase=f"round-{len(self._battle.rounds) + 1}",
                )
            )

        self._battle.ended_at = datetime.now()

        summary = self._build_summary(all_findings, all_mitigations)
        self._events.emit(
            BattleEndEvent(
                timestamp=datetime.now(),
                battle_id=self._battle.id,
                status=self._battle.status,
                summary=summary,
            )
        )

        return self.get_battle()

    async def _run_round(
        self,
        round_number: int,
        files: list[FileEntry],
        previous_findings: list[Finding],
        previous_mitigations: list[Mitigation],
    ) -> Round:
        display_round_start(round_number, self._config.rounds)

        self._events.emit(
            RoundStartEvent(timestamp=datetime.now(), round_number=round_number)
        )

        # --- Red Agent Turn ---
        display_red_header()
        red_output = ""

        red_context = AgentContext(
            scenario=self._config.scenario,
            files=files,
            previous_findings=previous_findings,
            previous_mitigations=previous_mitigations,
            round_number=round_number,
            role="red",
        )

        async for chunk in self._red_agent.analyze(red_context):
            if self._interrupted:
                break
            red_output += chunk
            display_red_chunk(chunk)
        display_agent_done()

        # Parse findings
        findings_result = parse_findings(red_output, round_number)
        findings = findings_result.value if findings_result.ok else []

        # Display structured findings
        for finding in findings:
            display_finding(finding)

        self._events.emit(
            AttackEvent(
                timestamp=datetime.now(),
                round_number=round_number,
                findings=findings,
            )
        )

        if self._interrupted:
            return Round(
                number=round_number,
                findings=findings,
                mitigations=[],
                red_raw_output=red_output,
                blue_raw_output="",
            )

        # --- Blue Agent Turn ---
        display_blue_header()
        blue_output = ""

        blue_context = AgentContext(
            scenario=self._config.scenario,
            files=files,
            previous_findings=previous_findings + findings,
            previous_mitigations=previous_mitigations,
            round_number=round_number,
            role="blue",
        )

        async for chunk in self._blue_agent.analyze(blue_context):
            if self._interrupted:
                break
            blue_output += chunk
            display_blue_chunk(chunk)
        display_agent_done()

        # Parse mitigations
        finding_ids = [f.id for f in findings]
        mitigations_result = parse_mitigations(blue_output, round_number, finding_ids)
        mitigations = mitigations_result.value if mitigations_result.ok else []

        # Display structured mitigations
        for mitigation in mitigations:
            display_mitigation(mitigation)

        self._events.emit(
            DefendEvent(
                timestamp=datetime.now(),
                round_number=round_number,
                mitigations=mitigations,
            )
        )

        display_round_end(round_number, len(findings), len(mitigations))

        self._events.emit(
            RoundEndEvent(
                timestamp=datetime.now(),
                round_number=round_number,
                finding_count=len(findings),
                mitigation_count=len(mitigations),
            )
        )

        return Round(
            number=round_number,
            findings=findings,
            mitigations=mitigations,
            red_raw_output=red_output,
            blue_raw_output=blue_output,
        )

    def _build_summary(
        self, findings: list[Finding], mitigations: list[Mitigation]
    ) -> BattleSummary:
        findings_by_severity: dict[str, int] = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for f in findings:
            findings_by_severity[f.severity] += 1

        return BattleSummary(
            total_rounds=len(self._battle.rounds),
            total_findings=len(findings),
            findings_by_severity=findings_by_severity,
            total_mitigations=len(mitigations),
            mitigation_coverage=(
                len(mitigations) / len(findings) if findings else 1.0
            ),
        )
