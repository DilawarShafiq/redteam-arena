"""
Agent interface -- defines the contract for Red and Blue agents.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from redteam_arena.types import AgentContext


class Agent(ABC):
    @abstractmethod
    async def analyze(self, context: AgentContext) -> AsyncIterator[str]:
        """Analyze the given context and yield streaming text chunks."""
        ...  # pragma: no cover
        # Make this a valid async generator
        if False:  # type: ignore[unreachable]
            yield ""
