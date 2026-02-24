/**
 * Battle engine — runs the Red vs Blue battle loop.
 * Alternates agent turns, tracks state, emits events.
 */

import { nanoid } from "nanoid";
import type {
  Battle,
  BattleConfig,
  BattleSummary,
  Finding,
  Mitigation,
  Round,
  Severity,
  FileEntry,
} from "../types.js";
import { BattleEventSystem } from "./event-system.js";
import { readCodebase, hasSourceFiles } from "./file-reader.js";
import type { Agent } from "../agents/agent.js";
import { parseFindings, parseMitigations } from "../agents/response-parser.js";
import {
  displayRedHeader,
  displayRedChunk,
  displayBlueHeader,
  displayBlueChunk,
  displayAgentDone,
  displayRoundStart,
  displayRoundEnd,
  displayFinding,
  displayMitigation,
} from "../display.js";

export interface BattleEngineOptions {
  redAgent: Agent;
  blueAgent: Agent;
  config: BattleConfig;
  onInterrupt?: () => void;
}

export class BattleEngine {
  private redAgent: Agent;
  private blueAgent: Agent;
  private config: BattleConfig;
  private events: BattleEventSystem;
  private battle: Battle;
  private interrupted = false;

  constructor(options: BattleEngineOptions) {
    this.redAgent = options.redAgent;
    this.blueAgent = options.blueAgent;
    this.config = options.config;
    this.events = new BattleEventSystem();

    this.battle = {
      id: nanoid(8),
      config: this.config,
      rounds: [],
      events: [],
      status: "pending",
      startedAt: new Date(),
    };
  }

  interrupt(): void {
    this.interrupted = true;
  }

  getBattle(): Battle {
    return {
      ...this.battle,
      events: [...this.events.getLog()],
    };
  }

  async run(): Promise<Battle> {
    // Read codebase
    const codeResult = await readCodebase(this.config.targetDir);
    if (!codeResult.ok) {
      throw new Error(codeResult.error.message);
    }

    const files = codeResult.value;
    if (!hasSourceFiles(files)) {
      throw new Error(
        `No source files found in ${this.config.targetDir}`
      );
    }

    // Start battle
    this.battle.status = "running";
    this.events.emit({
      type: "battle-start",
      timestamp: new Date(),
      data: {
        battleId: this.battle.id,
        scenario: this.config.scenario.name,
        targetDir: this.config.targetDir,
      },
    });

    const allFindings: Finding[] = [];
    const allMitigations: Mitigation[] = [];

    try {
      for (
        let roundNum = 1;
        roundNum <= this.config.rounds;
        roundNum++
      ) {
        if (this.interrupted) break;

        const round = await this.runRound(
          roundNum,
          files,
          allFindings,
          allMitigations
        );
        this.battle.rounds.push(round);
        allFindings.push(...round.findings);
        allMitigations.push(...round.mitigations);
      }

      if (this.interrupted) {
        this.battle.status = "interrupted";
      } else {
        this.battle.status = "completed";
      }
    } catch (err) {
      this.battle.status = "error";
      this.events.emit({
        type: "error",
        timestamp: new Date(),
        data: {
          message: err instanceof Error ? err.message : String(err),
          phase: `round-${this.battle.rounds.length + 1}`,
        },
      });
    }

    this.battle.endedAt = new Date();

    const summary = this.buildSummary(allFindings, allMitigations);
    this.events.emit({
      type: "battle-end",
      timestamp: new Date(),
      data: {
        battleId: this.battle.id,
        status: this.battle.status,
        summary,
      },
    });

    return this.getBattle();
  }

  private async runRound(
    roundNumber: number,
    files: FileEntry[],
    previousFindings: Finding[],
    previousMitigations: Mitigation[]
  ): Promise<Round> {
    displayRoundStart(roundNumber, this.config.rounds);

    this.events.emit({
      type: "round-start",
      timestamp: new Date(),
      data: { roundNumber },
    });

    // --- Red Agent Turn ---
    displayRedHeader();
    let redOutput = "";

    const redContext = {
      scenario: this.config.scenario,
      files,
      previousFindings,
      previousMitigations,
      roundNumber,
      role: "red" as const,
    };

    for await (const chunk of this.redAgent.analyze(redContext)) {
      if (this.interrupted) break;
      redOutput += chunk;
      displayRedChunk(chunk);
    }
    displayAgentDone();

    // Parse findings
    const findingsResult = parseFindings(redOutput, roundNumber);
    const findings = findingsResult.ok ? findingsResult.value : [];

    // Display structured findings
    for (const finding of findings) {
      displayFinding(finding);
    }

    this.events.emit({
      type: "attack",
      timestamp: new Date(),
      data: { roundNumber, findings },
    });

    if (this.interrupted) {
      return {
        number: roundNumber,
        findings,
        mitigations: [],
        redRawOutput: redOutput,
        blueRawOutput: "",
      };
    }

    // --- Blue Agent Turn ---
    displayBlueHeader();
    let blueOutput = "";

    const blueContext = {
      scenario: this.config.scenario,
      files,
      previousFindings: [...previousFindings, ...findings],
      previousMitigations,
      roundNumber,
      role: "blue" as const,
    };

    for await (const chunk of this.blueAgent.analyze(blueContext)) {
      if (this.interrupted) break;
      blueOutput += chunk;
      displayBlueChunk(chunk);
    }
    displayAgentDone();

    // Parse mitigations
    const findingIds = findings.map((f) => f.id);
    const mitigationsResult = parseMitigations(
      blueOutput,
      roundNumber,
      findingIds
    );
    const mitigations = mitigationsResult.ok
      ? mitigationsResult.value
      : [];

    // Display structured mitigations
    for (const mitigation of mitigations) {
      displayMitigation(mitigation);
    }

    this.events.emit({
      type: "defend",
      timestamp: new Date(),
      data: { roundNumber, mitigations },
    });

    displayRoundEnd(roundNumber, findings.length, mitigations.length);

    this.events.emit({
      type: "round-end",
      timestamp: new Date(),
      data: {
        roundNumber,
        findingCount: findings.length,
        mitigationCount: mitigations.length,
      },
    });

    return {
      number: roundNumber,
      findings,
      mitigations,
      redRawOutput: redOutput,
      blueRawOutput: blueOutput,
    };
  }

  private buildSummary(
    findings: Finding[],
    mitigations: Mitigation[]
  ): BattleSummary {
    const findingsBySeverity: Record<Severity, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0,
    };

    for (const f of findings) {
      findingsBySeverity[f.severity]++;
    }

    return {
      totalRounds: this.battle.rounds.length,
      totalFindings: findings.length,
      findingsBySeverity,
      totalMitigations: mitigations.length,
      mitigationCoverage:
        findings.length > 0
          ? mitigations.length / findings.length
          : 1,
    };
  }
}
