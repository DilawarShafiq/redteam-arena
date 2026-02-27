"""
Configuration file loader -- reads .redteamarena.yml or .redteamarena.json.
Merges project-level config with CLI arguments.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

import yaml

from redteam_arena.types import Err, Ok, ProviderId, ReportFormat, Result, Severity

CONFIG_FILES = [
    ".redteamarena.yml",
    ".redteamarena.yaml",
    ".redteamarena.json",
]

VALID_PROVIDERS = {"claude", "openai", "gemini", "ollama"}
VALID_FORMATS = {"markdown", "json", "sarif", "html"}
VALID_SEVERITIES = {"critical", "high", "medium", "low"}


@dataclass
class RedTeamConfig:
    provider: ProviderId | None = None
    model: str | None = None
    rounds: int | None = None
    scenario: str | None = None
    scenario_dir: str | None = None
    format: ReportFormat | None = None
    output: str | None = None
    fail_on: Severity | None = None


async def load_config(
    directory: str = "",
) -> Result[RedTeamConfig, Exception]:
    """Load config from .redteamarena.yml/.yaml/.json in the given directory."""
    search_dir = directory or os.getcwd()

    for filename in CONFIG_FILES:
        file_path = os.path.join(search_dir, filename)
        try:
            with open(file_path, encoding="utf-8") as f:
                raw = f.read()
        except OSError:
            continue

        try:
            if filename.endswith(".json"):
                data = json.loads(raw)
            else:
                data = yaml.safe_load(raw)

            if not data or not isinstance(data, dict):
                return Ok(value=RedTeamConfig())

            return Ok(value=_validate_config(data))
        except Exception as exc:
            return Err(error=Exception(f"Invalid config file {filename}: {exc}"))

    return Ok(value=RedTeamConfig())


def _validate_config(raw: dict) -> RedTeamConfig:
    """Validate and extract config fields."""
    config = RedTeamConfig()

    provider = raw.get("provider")
    if isinstance(provider, str) and provider in VALID_PROVIDERS:
        config.provider = provider  # type: ignore[assignment]

    model = raw.get("model")
    if isinstance(model, str):
        config.model = model

    rounds = raw.get("rounds")
    if isinstance(rounds, (int, float)) and rounds > 0:
        config.rounds = int(rounds)

    scenario = raw.get("scenario")
    if isinstance(scenario, str):
        config.scenario = scenario

    scenario_dir = raw.get("scenarioDir") or raw.get("scenario_dir")
    if isinstance(scenario_dir, str):
        config.scenario_dir = scenario_dir

    fmt = raw.get("format")
    if isinstance(fmt, str) and fmt in VALID_FORMATS:
        config.format = fmt  # type: ignore[assignment]

    output = raw.get("output")
    if isinstance(output, str):
        config.output = output

    fail_on = raw.get("failOn") or raw.get("fail_on")
    if isinstance(fail_on, str) and fail_on in VALID_SEVERITIES:
        config.fail_on = fail_on  # type: ignore[assignment]

    return config


def merge_config(
    file_config: RedTeamConfig,
    cli_options: dict,
) -> RedTeamConfig:
    """Merge file config with CLI options. CLI options take precedence."""
    merged = RedTeamConfig(
        provider=file_config.provider,
        model=file_config.model,
        rounds=file_config.rounds,
        scenario=file_config.scenario,
        scenario_dir=file_config.scenario_dir,
        format=file_config.format,
        output=file_config.output,
        fail_on=file_config.fail_on,
    )

    for key, value in cli_options.items():
        if value is not None and hasattr(merged, key):
            setattr(merged, key, value)

    return merged
