"""
Provider registry -- factory, detection, and validation for LLM providers.
"""

from __future__ import annotations

import os

from redteam_arena.agents.provider import Provider
from redteam_arena.types import ProviderId

PROVIDER_IDS: list[ProviderId] = ["claude", "openai", "gemini", "ollama"]

API_KEY_MAP: dict[str, str] = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "ollama": "",
}


def create_provider(
    provider_id: ProviderId,
    *,
    api_key: str | None = None,
    model: str = "",
    base_url: str | None = None,
) -> Provider:
    """Create a Provider instance by ID."""
    if provider_id == "claude":
        from redteam_arena.agents.claude_adapter import ClaudeAdapter

        return ClaudeAdapter(api_key=api_key, model=model)

    if provider_id in ("openai", "gemini", "ollama"):
        from redteam_arena.agents.openai_adapter import OpenAIAdapter

        return OpenAIAdapter(
            provider_id=provider_id,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

    raise ValueError(f"Unknown provider: {provider_id}")


def detect_provider() -> ProviderId:
    """Auto-detect the best available provider from environment."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return "claude"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    if os.environ.get("GOOGLE_API_KEY"):
        return "gemini"
    return "ollama"


def validate_provider(provider_id: ProviderId) -> tuple[bool, str]:
    """Validate that a provider's API key is available. Returns (valid, message)."""
    if provider_id == "ollama":
        return True, "Ollama uses local models (no API key needed)"

    env_var = API_KEY_MAP.get(provider_id, "")
    if not env_var:
        return False, f"Unknown provider: {provider_id}"

    if os.environ.get(env_var):
        return True, f"{provider_id} configured via {env_var}"

    return False, f"Missing {env_var} environment variable for {provider_id}"


def list_providers() -> list[dict[str, str]]:
    """List all providers with their status."""
    results = []
    for pid in PROVIDER_IDS:
        valid, message = validate_provider(pid)
        results.append({
            "id": pid,
            "status": "available" if valid else "missing-key",
            "message": message,
        })
    return results
