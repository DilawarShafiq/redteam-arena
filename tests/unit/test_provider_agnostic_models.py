"""Tests that no provider's model name is hardcoded into the agents.

Agents must never name a model. Each provider adapter owns its own default, so
an agent that injects one sends it to whichever provider the user configured --
which is how `--provider openai` ended up requesting a Claude model.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest

from redteam_arena.agents.auditor_agent import AuditorAgent
from redteam_arena.agents.blue_agent import BlueAgent
from redteam_arena.agents.provider import Provider
from redteam_arena.agents.red_agent import RedAgent
from redteam_arena.types import AgentContext, Message, Scenario, StreamOptions


class RecordingProvider(Provider):
    """Captures the StreamOptions each agent hands to the provider."""

    def __init__(self) -> None:
        self.seen: list[StreamOptions] = []

    async def stream(
        self, messages: list[Message], options: StreamOptions
    ) -> AsyncIterator[str]:
        self.seen.append(options)
        yield "[]"


def make_context(role: str) -> AgentContext:
    return AgentContext(
        scenario=Scenario(
            name="test",
            description="d",
            focus_areas=[],
            severity_guidance="",
            red_guidance="",
            blue_guidance="",
            is_meta=False,
            sub_scenarios=[],
        ),
        files=[],
        previous_findings=[],
        previous_mitigations=[],
        round_number=1,
        role=role,  # type: ignore[arg-type]
    )


async def drain(agent: object, context: AgentContext) -> None:
    async for _ in agent.analyze(context):  # type: ignore[attr-defined]
        pass


AGENTS = [
    ("red", RedAgent, "red"),
    ("blue", BlueAgent, "blue"),
    ("auditor", AuditorAgent, "red"),
]


class TestNoHardcodedModel:
    @pytest.mark.asyncio
    @pytest.mark.parametrize(("label", "agent_cls", "role"), AGENTS)
    async def test_agent_sends_no_model_by_default(
        self, label: str, agent_cls: type, role: str
    ) -> None:
        """With no --model, the agent must defer to the provider's default."""
        provider = RecordingProvider()
        agent = agent_cls(provider)

        await drain(agent, make_context(role))

        assert provider.seen, f"{label} agent never called the provider"
        assert provider.seen[0].model == "", (
            f"{label} agent injected model {provider.seen[0].model!r}; "
            "it must send an empty string so the provider chooses"
        )

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("label", "agent_cls", "role"), AGENTS)
    async def test_agent_forwards_explicit_model(
        self, label: str, agent_cls: type, role: str
    ) -> None:
        provider = RecordingProvider()
        agent = agent_cls(provider, model="gpt-4o")

        await drain(agent, make_context(role))

        assert provider.seen[0].model == "gpt-4o"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(("label", "agent_cls", "role"), AGENTS)
    async def test_no_vendor_name_leaks_into_options(
        self, label: str, agent_cls: type, role: str
    ) -> None:
        """Guards against any vendor default creeping back in."""
        provider = RecordingProvider()
        agent = agent_cls(provider)

        await drain(agent, make_context(role))

        model = provider.seen[0].model.lower()
        for vendor in ("claude", "gpt", "gemini", "llama"):
            assert vendor not in model, f"{label} agent hardcodes a {vendor} model"


class TestProviderDefaults:
    """Each adapter owns its own default -- that is the right layer for it."""

    def test_openai_adapter_defaults_per_provider(self) -> None:
        from redteam_arena.agents.openai_adapter import DEFAULT_MODELS

        assert DEFAULT_MODELS["openai"].startswith("gpt")
        assert DEFAULT_MODELS["gemini"].startswith("gemini")
        assert DEFAULT_MODELS["ollama"]

    def test_claude_adapter_has_its_own_default(self) -> None:
        from redteam_arena.agents.claude_adapter import DEFAULT_MODEL

        assert DEFAULT_MODEL.startswith("claude")
