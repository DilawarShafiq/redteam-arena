/**
 * Agent interface — defines the contract for Red and Blue agents.
 */

import type { AgentContext } from "../types.js";

export interface Agent {
  analyze(context: AgentContext): AsyncIterable<string>;
}
