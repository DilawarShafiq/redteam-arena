"""
Red Agent -- attacker. Analyzes source code to find vulnerabilities.
Composes a Provider for LLM streaming.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from redteam_arena.agents.agent import Agent
from redteam_arena.agents.provider import Provider
from redteam_arena.core.file_reader import format_files_for_prompt
from redteam_arena.types import AgentContext, Message, StreamOptions

RED_SYSTEM_PROMPT = """You are a senior security researcher performing a static code analysis.
Your goal is to find real, exploitable vulnerabilities in the provided source code.

RULES:
- Only report vulnerabilities you can clearly see in the code
- Reference specific file paths and line numbers
- Rate severity accurately: Critical > High > Medium > Low
- Explain the attack vector clearly
- Do NOT fabricate vulnerabilities that don't exist in the code
- Focus on the scenario's specific attack category

After your analysis, output your findings as a JSON block:

```json
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
```

If you find no vulnerabilities for this round, output an empty array: ```json\n[]\n```"""


class RedAgent(Agent):
    def __init__(self, provider: Provider) -> None:
        self._provider = provider

    async def analyze(self, context: AgentContext) -> AsyncIterator[str]:
        system_prompt = _build_red_system_prompt(context)
        messages = _build_red_messages(context)

        async for chunk in self._provider.stream(
            messages,
            StreamOptions(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system_prompt=system_prompt,
            ),
        ):
            yield chunk


def _build_red_system_prompt(context: AgentContext) -> str:
    prompt = RED_SYSTEM_PROMPT

    if context.scenario.red_guidance:
        prompt += f"\n\n## Scenario-Specific Guidance\n\n{context.scenario.red_guidance}"

    if context.scenario.focus_areas:
        areas = "\n".join(f"- {a}" for a in context.scenario.focus_areas)
        prompt += f"\n\n## Focus Areas\n\nLook specifically for:\n{areas}"

    if context.scenario.severity_guidance:
        prompt += f"\n\n## Severity Rating Guide\n\n{context.scenario.severity_guidance}"

    return prompt


def _build_red_messages(context: AgentContext) -> list[Message]:
    messages: list[Message] = []

    code_context = format_files_for_prompt(context.files)
    user_message = f"## Target Codebase\n\n{code_context}"

    if context.previous_findings:
        user_message += "\n\n## Previously Found Vulnerabilities (do NOT repeat these)\n\n"
        for f in context.previous_findings:
            user_message += (
                f"- [{f.severity.upper()}] {f.file_path}:{f.line_reference} "
                f"-- {f.description}\n"
            )
        user_message += "\nFind NEW vulnerabilities not listed above. Look deeper into the code."
    else:
        user_message += (
            f"\n\nAnalyze this codebase for {context.scenario.name} vulnerabilities. "
            f"This is round {context.round_number}."
        )

    messages.append(Message(role="user", content=user_message))
    return messages
