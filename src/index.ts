/**
 * RedTeam Arena — AI vs AI adversarial security testing.
 * Programmatic API entry point.
 */

export { BattleEngine } from "./core/battle-engine.js";
export type { BattleEngineOptions } from "./core/battle-engine.js";
export { BattleEventSystem } from "./core/event-system.js";
export { readCodebase, formatFilesForPrompt, hasSourceFiles } from "./core/file-reader.js";
export { ClaudeAdapter, validateApiKey } from "./agents/claude-adapter.js";
export { RedAgent } from "./agents/red-agent.js";
export { BlueAgent } from "./agents/blue-agent.js";
export { parseFindings, parseMitigations } from "./agents/response-parser.js";
export { loadScenario, listScenarios } from "./scenarios/scenario.js";
export { generateReport, writeReport } from "./reports/battle-report.js";
export type {
  Battle,
  BattleConfig,
  BattleEvent,
  BattleStatus,
  BattleSummary,
  Finding,
  Mitigation,
  Round,
  Scenario,
  Severity,
  FileEntry,
  AgentContext,
  StreamOptions,
  Message,
  Result,
} from "./types.js";
export type { Agent } from "./agents/agent.js";
export type { Provider } from "./agents/provider.js";
