/**
 * Core type definitions for RedTeam Arena.
 * All entities, events, and configuration types.
 */

// --- Severity ---

export type Severity = "critical" | "high" | "medium" | "low";

// --- Finding ---

export interface Finding {
  id: string;
  roundNumber: number;
  filePath: string;
  lineReference: string;
  description: string;
  attackVector: string;
  severity: Severity;
  codeSnippet?: string;
}

// --- Mitigation ---

export interface Mitigation {
  id: string;
  findingId: string;
  roundNumber: number;
  acknowledgment: string;
  proposedFix: string;
  confidence: "high" | "medium" | "low";
}

// --- Round ---

export interface Round {
  number: number;
  findings: Finding[];
  mitigations: Mitigation[];
  redRawOutput: string;
  blueRawOutput: string;
}

// --- Scenario ---

export interface Scenario {
  name: string;
  description: string;
  focusAreas: string[];
  severityGuidance: string;
  redGuidance: string;
  blueGuidance: string;
  isMeta?: boolean;
  subScenarios?: string[];
}

// --- File Entry ---

export interface FileEntry {
  path: string;
  content: string;
}

// --- Agent Context ---

export interface AgentContext {
  scenario: Scenario;
  files: FileEntry[];
  previousFindings: Finding[];
  previousMitigations: Mitigation[];
  roundNumber: number;
  role: "red" | "blue";
}

// --- Stream Options ---

export interface StreamOptions {
  model: string;
  maxTokens: number;
  systemPrompt: string;
}

// --- Messages ---

export interface Message {
  role: "user" | "assistant";
  content: string;
}

// --- Battle Status ---

export type BattleStatus =
  | "pending"
  | "running"
  | "completed"
  | "interrupted"
  | "error";

// --- Battle Config ---

export interface BattleConfig {
  targetDir: string;
  scenario: Scenario;
  rounds: number;
}

// --- Battle Event (discriminated union) ---

export type BattleEvent =
  | {
      type: "battle-start";
      timestamp: Date;
      data: { battleId: string; scenario: string; targetDir: string };
    }
  | {
      type: "round-start";
      timestamp: Date;
      data: { roundNumber: number };
    }
  | {
      type: "attack";
      timestamp: Date;
      data: { roundNumber: number; findings: Finding[] };
    }
  | {
      type: "defend";
      timestamp: Date;
      data: { roundNumber: number; mitigations: Mitigation[] };
    }
  | {
      type: "round-end";
      timestamp: Date;
      data: {
        roundNumber: number;
        findingCount: number;
        mitigationCount: number;
      };
    }
  | {
      type: "battle-end";
      timestamp: Date;
      data: { battleId: string; status: BattleStatus; summary: BattleSummary };
    }
  | {
      type: "error";
      timestamp: Date;
      data: { message: string; phase: string };
    };

// --- Battle Summary ---

export interface BattleSummary {
  totalRounds: number;
  totalFindings: number;
  findingsBySeverity: Record<Severity, number>;
  totalMitigations: number;
  mitigationCoverage: number;
}

// --- Battle ---

export interface Battle {
  id: string;
  config: BattleConfig;
  rounds: Round[];
  events: BattleEvent[];
  status: BattleStatus;
  startedAt: Date;
  endedAt?: Date;
}

// --- Result type for error handling ---

export type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E };
