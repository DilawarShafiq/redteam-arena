"""
OpenAI-compatible adapter -- supports OpenAI, Gemini, and Ollama.
Uses the openai Python SDK with configurable base_url.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

from redteam_arena.agents.provider import Provider
from redteam_arena.types import Message, ProviderId, StreamOptions

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o",
    "gemini": "gemini-2.0-flash",
    "ollama": "llama3.2",
}

BASE_URLS: dict[str, str] = {
    "openai": "https://api.openai.com/v1",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/",
    "ollama": "http://localhost:11434/v1",
}

API_KEY_ENV: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "ollama": "",
}


class OpenAIAdapter(Provider):
    def __init__(
        self,
        provider_id: ProviderId = "openai",
        api_key: str | None = None,
        model: str = "",
        base_url: str | None = None,
    ) -> None:
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise ImportError(
                "openai package required for OpenAI/Gemini/Ollama providers. "
                "Install with: pip install openai"
            ) from exc

        self._provider_id = provider_id
        self._model = model or DEFAULT_MODELS.get(provider_id, "gpt-4o")

        resolved_key = api_key
        if not resolved_key:
            env_var = API_KEY_ENV.get(provider_id, "")
            resolved_key = os.environ.get(env_var, "") if env_var else "ollama"

        resolved_base = base_url
        if not resolved_base:
            if provider_id == "ollama":
                resolved_base = os.environ.get(
                    "OLLAMA_BASE_URL", BASE_URLS["ollama"]
                )
            else:
                resolved_base = BASE_URLS.get(provider_id)

        self._client = AsyncOpenAI(
            api_key=resolved_key,
            base_url=resolved_base,
        )

    async def stream(
        self, messages: list[Message], options: StreamOptions
    ) -> AsyncIterator[str]:
        openai_messages: list[dict] = [
            {"role": "system", "content": options.system_prompt},
        ]
        for m in messages:
            openai_messages.append({"role": m.role, "content": m.content})

        model = options.model or self._model

        response = await self._client.chat.completions.create(
            model=model,
            max_tokens=options.max_tokens,
            messages=openai_messages,  # type: ignore[arg-type]
            stream=True,
        )

        async for chunk in response:  # type: ignore[union-attr]
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
