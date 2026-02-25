"""
LLM Provider interface -- provider-agnostic streaming abstraction.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from redteam_arena.types import Message, StreamOptions


class Provider(ABC):
    @abstractmethod
    async def stream(
        self, messages: list[Message], options: StreamOptions
    ) -> AsyncIterator[str]:
        """Stream LLM response text chunks."""
        ...  # pragma: no cover
        if False:  # type: ignore[unreachable]
            yield ""
