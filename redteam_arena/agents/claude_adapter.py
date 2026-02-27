"""
Claude adapter -- implements Provider interface using the anthropic Python SDK.
Streams responses via the messages API.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import anthropic

from redteam_arena.agents.provider import Provider
from redteam_arena.types import Message, StreamOptions

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeAdapter(Provider):
    def __init__(self, api_key: str | None = None, model: str = "") -> None:
        self._model = model
        self._client = anthropic.Anthropic(
            api_key=api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
        )

    async def stream(
        self, messages: list[Message], options: StreamOptions
    ) -> AsyncIterator[str]:
        anthropic_messages = [
            {"role": m.role, "content": m.content} for m in messages
        ]

        with self._client.messages.stream(
            model=options.model or self._model or DEFAULT_MODEL,
            max_tokens=options.max_tokens,
            system=options.system_prompt,
            messages=anthropic_messages,  # type: ignore[arg-type]
        ) as stream:
            for text in stream.text_stream:
                yield text


def validate_api_key() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))
