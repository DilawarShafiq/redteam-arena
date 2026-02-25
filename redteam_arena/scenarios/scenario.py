"""
Scenario type definition and Markdown frontmatter loader.
Parses scenario files: YAML frontmatter + Red/Blue guidance sections.
"""

from __future__ import annotations

import os
import re

import yaml

from redteam_arena.types import Scenario, Ok, Err, Result

# The builtin scenarios directory is alongside this module
BUILTIN_DIR = os.path.join(os.path.dirname(__file__), "builtin")


def _parse_frontmatter(
    raw: str,
) -> Result[tuple[dict, str], Exception]:
    """Parse YAML frontmatter and body from a scenario markdown file."""
    parts = raw.split("---")
    if len(parts) < 3:
        return Err(
            error=Exception(
                "Invalid scenario file: missing --- frontmatter delimiters"
            )
        )

    yaml_content = parts[1].strip()
    body = "---".join(parts[2:]).strip()

    try:
        frontmatter = yaml.safe_load(yaml_content)
        if not isinstance(frontmatter, dict):
            return Err(error=Exception("Invalid scenario frontmatter: not a mapping"))
        if not frontmatter.get("name") or not frontmatter.get("description"):
            return Err(
                error=Exception(
                    "Invalid scenario frontmatter: missing name or description"
                )
            )
        return Ok(value=(frontmatter, body))
    except yaml.YAMLError as exc:
        return Err(error=Exception(f"Failed to parse scenario YAML: {exc}"))


def _parse_guidance_sections(body: str) -> tuple[str, str]:
    """Extract Red and Blue agent guidance sections from the body."""
    red_guidance = ""
    blue_guidance = ""

    red_match = re.search(
        r"## Red Agent Guidance\s*\n([\s\S]*?)(?=## Blue Agent Guidance|$)", body
    )
    blue_match = re.search(r"## Blue Agent Guidance\s*\n([\s\S]*?)$", body)

    if red_match:
        red_guidance = red_match.group(1).strip()
    if blue_match:
        blue_guidance = blue_match.group(1).strip()

    return red_guidance, blue_guidance


async def load_scenario(name: str) -> Result[Scenario, Exception]:
    """Load a scenario by name from the builtin directory."""
    file_path = os.path.join(BUILTIN_DIR, f"{name}.md")

    raw: str | None = None
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw = f.read()
    except OSError:
        pass

    if raw is None:
        return Err(error=Exception(f"Scenario not found: {name}"))

    parsed = _parse_frontmatter(raw)
    if not parsed.ok:
        return parsed  # type: ignore[return-value]

    frontmatter, body = parsed.value
    red_guidance, blue_guidance = _parse_guidance_sections(body)

    return Ok(
        value=Scenario(
            name=frontmatter["name"],
            description=frontmatter["description"],
            focus_areas=frontmatter.get("focus_areas", []),
            severity_guidance=frontmatter.get("severity_guidance", ""),
            red_guidance=red_guidance,
            blue_guidance=blue_guidance,
            is_meta=frontmatter.get("is_meta", False),
            sub_scenarios=frontmatter.get("sub_scenarios", []),
        )
    )


async def list_scenarios() -> list[Scenario]:
    """List all available builtin scenarios."""
    scenarios: list[Scenario] = []

    try:
        files = sorted(os.listdir(BUILTIN_DIR))
        for filename in files:
            if not filename.endswith(".md"):
                continue
            name = filename.replace(".md", "")
            result = await load_scenario(name)
            if result.ok:
                # Avoid duplicates
                if not any(s.name == result.value.name for s in scenarios):
                    scenarios.append(result.value)
    except OSError:
        pass

    return scenarios
