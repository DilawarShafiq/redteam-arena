/**
 * Blue Agent — defender. Proposes mitigations for Red agent findings.
 * Composes a Provider for LLM streaming.
 */

import type { Agent } from "./agent.js";
import type { Provider } from "./provider.js";
import type { AgentContext, Message } from "../types.js";
import { formatFilesForPrompt } from "../core/file-reader.js";

const BLUE_SYSTEM_PROMPT = `You are a senior security engineer reviewing vulnerability findings and proposing mitigations.
Your goal is to assess each finding and provide concrete, actionable fixes.

RULES:
- Acknowledge each finding honestly (don't dismiss valid vulnerabilities)
- Propose specific code-level fixes, not vague recommendations
- Rate your confidence: high (certain fix), medium (likely fix), low (needs investigation)
- Reference the specific files and lines from the findings
- Provide code examples for fixes when possible

After your analysis, output your mitigations as a JSON block:

\`\`\`json
[
  {
    "findingId": "id-from-finding",
    "acknowledgment": "Assessment of the finding",
    "proposedFix": "Specific code-level mitigation with example",
    "confidence": "high"
  }
]
\`\`\``;

export class BlueAgent implements Agent {
  private provider: Provider;

  constructor(provider: Provider) {
    this.provider = provider;
  }

  async *analyze(context: AgentContext): AsyncIterable<string> {
    const systemPrompt = buildBlueSystemPrompt(context);
    const messages = buildBlueMessages(context);

    yield* this.provider.stream(messages, {
      model: "claude-sonnet-4-20250514",
      maxTokens: 4096,
      systemPrompt,
    });
  }
}

function buildBlueSystemPrompt(context: AgentContext): string {
  let prompt = BLUE_SYSTEM_PROMPT;

  if (context.scenario.blueGuidance) {
    prompt += `\n\n## Scenario-Specific Guidance\n\n${context.scenario.blueGuidance}`;
  }

  return prompt;
}

function buildBlueMessages(context: AgentContext): Message[] {
  const messages: Message[] = [];

  // Include codebase for reference
  const codeContext = formatFilesForPrompt(context.files);
  let userMessage = `## Target Codebase (for reference)\n\n${codeContext}`;

  // Include the findings to mitigate
  const currentFindings = context.previousFindings.filter(
    (f) => f.roundNumber === context.roundNumber
  );

  if (currentFindings.length > 0) {
    userMessage += `\n\n## Vulnerabilities Found This Round\n\nThe Red agent found the following vulnerabilities. Assess each one and propose mitigations:\n\n`;

    for (const f of currentFindings) {
      userMessage += `### Finding: ${f.id}\n`;
      userMessage += `- **File**: ${f.filePath}:${f.lineReference}\n`;
      userMessage += `- **Severity**: ${f.severity.toUpperCase()}\n`;
      userMessage += `- **Description**: ${f.description}\n`;
      userMessage += `- **Attack Vector**: ${f.attackVector}\n`;
      if (f.codeSnippet) {
        userMessage += `- **Code**: \`${f.codeSnippet}\`\n`;
      }
      userMessage += "\n";
    }
  } else {
    userMessage += `\n\nNo new vulnerabilities found in this round. Summarize the overall security posture.`;
  }

  // Include previous mitigations for context
  if (context.previousMitigations.length > 0) {
    userMessage += `\n\n## Previously Proposed Mitigations\n\n`;
    for (const m of context.previousMitigations) {
      userMessage += `- [${m.confidence.toUpperCase()}] ${m.proposedFix.slice(0, 100)}...\n`;
    }
  }

  messages.push({ role: "user", content: userMessage });

  return messages;
}
