# Contributing to RedTeam Arena

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Fork and clone
git clone https://github.com/<your-username>/redteam-arena.git
cd redteam-arena

# Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run the CLI directly
redteam-arena --help
```

## Development Commands

| Command | Description |
|---------|-------------|
| `pytest` | Run all tests |
| `pytest tests/unit/` | Run unit tests only |
| `pytest tests/integration/` | Run integration tests only |
| `pytest -v --tb=short` | Verbose output with short tracebacks |
| `ruff check redteam_arena/` | Lint source files |
| `ruff check --fix redteam_arena/` | Auto-fix lint issues |
| `mypy redteam_arena/` | Type-check without running |

## Project Structure

```
redteam_arena/
├── agents/          # Red and Blue agent implementations
│   ├── red_agent.py
│   ├── blue_agent.py
│   ├── claude_adapter.py
│   ├── openai_adapter.py
│   ├── provider_registry.py
│   └── response_parser.py
├── core/            # Battle engine and supporting systems
│   ├── battle_engine.py
│   ├── event_system.py
│   ├── file_reader.py
│   ├── battle_store.py
│   ├── config.py
│   └── ...
├── scenarios/       # Scenario loader + built-in scenarios
│   ├── scenario.py
│   └── builtin/     # Markdown scenario definitions (.md)
├── reports/         # Report generators (Markdown, JSON, SARIF, HTML)
├── server/          # FastAPI REST + WebSocket server
├── cli.py           # CLI entry point (click)
├── display.py       # Terminal output formatting (rich)
├── __init__.py      # Programmatic API exports
└── types.py         # Shared dataclasses and types
tests/
├── unit/            # Unit tests per module
└── integration/     # End-to-end battle flow tests
```

## How to Add a New Scenario

1. Create a new Markdown file in `redteam_arena/scenarios/builtin/`:

```markdown
---
name: my-scenario
description: Short description of what this checks
tags:
  - owasp
  - web
focus_areas:
  - Pattern to look for
  - Another pattern
severity_guidance: >
  Critical: direct, exploitable risk with full impact
  High: significant risk, likely exploitable
  Medium: moderate risk, requires specific conditions
  Low: minor risk or defense-in-depth issue
---

## Red Agent Guidance

Instructions for the attacker agent. Be specific about what attack
vectors to look for and how to identify them in code.

## Blue Agent Guidance

Instructions for the defender agent. Describe concrete mitigations,
code patterns to use, and how to validate the fix.
```

2. Verify it appears with `redteam-arena list`
3. Add a test in `tests/unit/test_scenario.py`

## Pull Request Guidelines

- **One feature per PR** — keep changes focused
- **Tests required** — all new code needs tests
- **Lint must pass** — `ruff check redteam_arena/` with zero errors
- **Follow existing patterns** — look at similar code in the codebase
- **Update docs** if you change CLI options or public API

## Branch Naming

- `feat/short-description` — new features
- `fix/short-description` — bug fixes
- `docs/short-description` — documentation only

## Need Help?

Open an issue with the `question` label, or start a discussion.
