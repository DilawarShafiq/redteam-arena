"""
Auditor Agent -- compliance and architecture reviewer.
Performs NIST, SOC2, FedRAMP, ISO 27001, and ISO 42001 (AI) compliance checks.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from redteam_arena.agents.agent import Agent
from redteam_arena.agents.provider import Provider
from redteam_arena.core.file_reader import format_files_for_prompt
from redteam_arena.types import AgentContext, Message, StreamOptions

AUDITOR_SYSTEM_PROMPT = """You are a Principal Compliance Auditor at an elite enterprise audit firm.
Your goal is to perform a rigorous, unforgiving compliance and security architecture audit of the provided source code and configuration.

FRAMEWORKS IN SCOPE (Depending on scenario):
- SOC 2 (Security, Availability, Processing Integrity, Confidentiality, Privacy)
- FedRAMP / NIST 800-53
- ISO 27001 (Information Security) & ISO 42001 (AI Management Systems)
- PCI DSS
- Healthcare (HIPAA, HITECH, HITRUST, EPCS DEA)
- OWASP Top 10 & OWASP LLM Top 10

RULES:
- Evaluate the code for control gaps, insecure configurations, and architectural flaws.
- ENFORCE ZERO TRUST: If you see external-facing portals, administrative functions, or sensitive data access WITHOUT explicit proof of Multi-Factor Authentication (MFA), strict session invalidation, and strict RBAC, you MUST flag it as a Critical or High control failure.
- Reference specific file paths and line numbers.
- Rate severity accurately: Critical > High > Medium > Low.
- Explain the compliance violation clearly in the 'attackVector' field (which serves as 'control failure' in this context).
- Focus strictly on the required compliance frameworks or security standards.

After your analysis, output your findings as a JSON block:

```json
[
  {
    "filePath": "relative/path/to/file.ts",
    "lineReference": "45",
    "description": "SOC2 CC6.1 - Hardcoded credentials or insecure secrets management.",
    "attackVector": "Violation of access control and secure storage. Threat actors could extract these secrets.",
    "severity": "critical",
    "codeSnippet": "the non-compliant code"
  }
]
```

If you find no compliance violations or control gaps, output an empty array: ```json\n[]\n```"""


class AuditorAgent(Agent):
    def __init__(self, provider: Provider, *, model: str = "") -> None:
        self._provider = provider
        self._model = model

    async def analyze(self, context: AgentContext) -> AsyncIterator[str]:
        system_prompt = _build_auditor_system_prompt(context)
        messages = _build_auditor_messages(context)

        async for chunk in self._provider.stream(
            messages,
            StreamOptions(
                model=self._model or "claude-3-7-sonnet-20250219",
                max_tokens=4096,
                system_prompt=system_prompt,
            ),
        ):
            yield chunk


def _build_auditor_system_prompt(context: AgentContext) -> str:
    prompt = AUDITOR_SYSTEM_PROMPT

    if context.scenario.red_guidance:
        # We reuse red_guidance for the auditor's specific audit instructions
        prompt += f"\n\n## Audit Scope & Guidance\n\n{context.scenario.red_guidance}"

    if context.scenario.focus_areas:
        areas = "\n".join(f"- {a}" for a in context.scenario.focus_areas)
        prompt += f"\n\n## Focus Areas\n\nLook specifically for:\n{areas}"

    if context.scenario.severity_guidance:
        prompt += f"\n\n## Severity Rating Guide\n\n{context.scenario.severity_guidance}"

    return prompt


def _build_auditor_messages(context: AgentContext) -> list[Message]:
    messages: list[Message] = []

    code_context = format_files_for_prompt(context.files)
    user_message = f"## Target Architecture & Codebase\n\n{code_context}"

    if context.previous_findings:
        user_message += "\n\n## Previously Found Control Gaps (do NOT repeat these)\n\n"
        for f in context.previous_findings:
            user_message += (
                f"- [{f.severity.upper()}] {f.file_path}:{f.line_reference} "
                f"-- {f.description}\n"
            )
        user_message += "\nFind NEW compliance violations not listed above. Look deeper into the architecture."
    else:
        user_message += (
            f"\n\nPerform a comprehensive {context.scenario.name} compliance audit on this codebase. "
            f"This is audit phase {context.round_number}."
        )

    messages.append(Message(role="user", content=user_message))
    return messages
