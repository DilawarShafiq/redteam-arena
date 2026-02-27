"""
Blue Agent -- defender. Proposes mitigations for Red agent findings.
Composes a Provider for LLM streaming.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from redteam_arena.agents.agent import Agent
from redteam_arena.agents.provider import Provider
from redteam_arena.core.file_reader import format_files_for_prompt
from redteam_arena.types import AgentContext, Message, StreamOptions

BLUE_SYSTEM_PROMPT = """You are a senior security engineer reviewing vulnerability findings and proposing mitigations.
Your goal is to assess each finding and provide concrete, actionable fixes.

RULES:
- Acknowledge each finding honestly (don't dismiss valid vulnerabilities)
- Propose specific code-level fixes, not vague recommendations
- Rate your confidence: high (certain fix), medium (likely fix), low (needs investigation)
- Reference the specific files and lines from the findings
- Provide code examples for fixes when possible

After your analysis, output your mitigations as a JSON block:

```json
[
  {
    "findingId": "id-from-finding",
    "acknowledgment": "Assessment of the finding",
    "proposedFix": "Specific code-level mitigation with example",
    "confidence": "high"
  }
]
```"""


class BlueAgent(Agent):
    def __init__(self, provider: Provider, *, model: str = "") -> None:
        self._provider = provider
        self._model = model

    async def analyze(self, context: AgentContext) -> AsyncIterator[str]:
        system_prompt = _build_blue_system_prompt(context)
        messages = _build_blue_messages(context)

        async for chunk in self._provider.stream(
            messages,
            StreamOptions(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system_prompt=system_prompt,
            ),
        ):
            yield chunk


def _build_blue_system_prompt(context: AgentContext) -> str:
    prompt = BLUE_SYSTEM_PROMPT

    if context.scenario.blue_guidance:
        prompt += f"\n\n## Scenario-Specific Guidance\n\n{context.scenario.blue_guidance}"

    return prompt


def _build_blue_messages(context: AgentContext) -> list[Message]:
    messages: list[Message] = []

    code_context = format_files_for_prompt(context.files)
    user_message = f"## Target Codebase (for reference)\n\n{code_context}"

    # Include the findings to mitigate
    current_findings = [
        f for f in context.previous_findings if f.round_number == context.round_number
    ]

    if current_findings:
        user_message += (
            "\n\n## Vulnerabilities Found This Round\n\n"
            "The Red agent found the following vulnerabilities. "
            "Assess each one and propose mitigations:\n\n"
        )
        for f in current_findings:
            user_message += f"### Finding: {f.id}\n"
            user_message += f"- **File**: {f.file_path}:{f.line_reference}\n"
            user_message += f"- **Severity**: {f.severity.upper()}\n"
            user_message += f"- **Description**: {f.description}\n"
            user_message += f"- **Attack Vector**: {f.attack_vector}\n"
            if f.code_snippet:
                user_message += f"- **Code**: `{f.code_snippet}`\n"
            user_message += "\n"
    else:
        user_message += (
            "\n\nNo new vulnerabilities found in this round. "
            "Summarize the overall security posture."
        )

    # Include previous mitigations for context
    if context.previous_mitigations:
        user_message += "\n\n## Previously Proposed Mitigations\n\n"
        for m in context.previous_mitigations:
            user_message += (
                f"- [{m.confidence.upper()}] {m.proposed_fix[:100]}...\n"
            )

    messages.append(Message(role="user", content=user_message))
    return messages
