"""
Mock Provider for testing and demonstrations.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

from redteam_arena.agents.provider import Provider
from redteam_arena.types import Message, StreamOptions

MOCK_RESPONSE = r"""Certainly! I have audited the codebase and found several SOC 2 and compliance gaps.

```json
[
  {
    "filePath": "app.py",
    "lineReference": "4",
    "description": "SOC2 CC6.1 - Hardcoded database credentials detected.",
    "attackVector": "Unauthorized access to the backend database. Credentials can be extracted from source control.",
    "severity": "critical",
    "codeSnippet": "DB_PASSWORD = \"supersecret_testpassword\""
  },
  {
    "filePath": "app.py",
    "lineReference": "18",
    "description": "FedRAMP SC-13 - Non-FIPS compliant hashing algorithm (MD5).",
    "attackVector": "MD5 is cryptographically broken and forbidden in federal environments. Susceptible to collision attacks.",
    "severity": "high",
    "codeSnippet": "hashlib.md5(uid.encode())"
  }
]
```"""

class MockProvider(Provider):
    async def stream(
        self,
        messages: list[Message],
        options: StreamOptions
    ) -> AsyncIterator[str]:
        # Simulate streaming delay
        for chunk in MOCK_RESPONSE.split(" "):
            await asyncio.sleep(0.01)
            yield chunk + " "
