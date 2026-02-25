/**
 * Red Agent — attacker. Analyzes source code to find vulnerabilities.
 * Composes a Provider for LLM streaming.
 */

import type { Agent } from "./agent.js";
import type { Provider } from "./provider.js";
import type { AgentContext, Message } from "../types.js";
import { formatFilesForPrompt } from "../core/file-reader.js";

const RED_SYSTEM_PROMPT = `You are a senior security researcher performing a static code analysis.
Your goal is to find real, exploitable vulnerabilities in the provided source code.

RULES:
- Only report vulnerabilities you can clearly see in the code
- Reference specific file paths and line numbers
- Rate severity accurately: Critical > High > Medium > Low
- Explain the attack vector clearly
- Do NOT fabricate vulnerabilities that don't exist in the code
- Focus on the scenario's specific attack category

After your analysis, output your findings as a JSON block:

\`\`\`json
[
  {
    "filePath": "relative/path/to/file.ts",
    "lineReference": "12",
    "description": "Clear description of the vulnerability",
    "attackVector": "How this can be exploited",
    "severity": "high",
    "codeSnippet": "the vulnerable code"
  }
]
\`\`\`

If you find no vulnerabilities for this round, output an empty array: \`\`\`json\n[]\n\`\`\``;

export class RedAgent implements Agent {
  private provider: Provider;

  constructor(provider: Provider) {
    this.provider = provider;
  }

  async *analyze(context: AgentContext): AsyncIterable<string> {
    const systemPrompt = buildRedSystemPrompt(context);
    const messages = buildRedMessages(context);

    yield* this.provider.stream(messages, {
      model: "claude-sonnet-4-20250514",
      maxTokens: 4096,
      systemPrompt,
    });
  }
}

function buildRedSystemPrompt(context: AgentContext): string {
  let prompt = RED_SYSTEM_PROMPT;

  if (context.scenario.redGuidance) {
    prompt += `\n\n## Scenario-Specific Guidance\n\n${context.scenario.redGuidance}`;
  }

  if (context.scenario.focusAreas.length > 0) {
    prompt += `\n\n## Focus Areas\n\nLook specifically for:\n${context.scenario.focusAreas.map((a) => `- ${a}`).join("\n")}`;
  }

  if (context.scenario.severityGuidance) {
    prompt += `\n\n## Severity Rating Guide\n\n${context.scenario.severityGuidance}`;
  }

  return prompt;
}

function buildRedMessages(context: AgentContext): Message[] {
  const messages: Message[] = [];

  // Include codebase
  const codeContext = formatFilesForPrompt(context.files);
  let userMessage = `## Target Codebase\n\n${codeContext}`;

  // Include previous findings context for subsequent rounds
  if (context.previousFindings.length > 0) {
    userMessage += `\n\n## Previously Found Vulnerabilities (do NOT repeat these)\n\n`;
    for (const f of context.previousFindings) {
      userMessage += `- [${f.severity.toUpperCase()}] ${f.filePath}:${f.lineReference} — ${f.description}\n`;
    }
    userMessage += `\nFind NEW vulnerabilities not listed above. Look deeper into the code.`;
  } else {
    userMessage += `\n\nAnalyze this codebase for ${context.scenario.name} vulnerabilities. This is round ${context.roundNumber}.`;
  }

  messages.push({ role: "user", content: userMessage });

  return messages;
}
