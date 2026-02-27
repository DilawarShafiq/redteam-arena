---
id: "003"
title: "v0.0.1 Launch Polish All Files"
stage: general
date: "2026-02-27"
surface: agent
model: claude-sonnet-4-6
feature: none
branch: main
user: DilawarGopang
command: "Find and complete the remaining things to launch its 0.0.1 as the best opensource, the dev AI world should love it"
labels: ["release", "launch", "polish", "v0.0.1", "readme", "ci", "tests"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - pyproject.toml
  - redteam_arena/cli.py
  - redteam_arena/server/api_server.py
  - redteam_arena/core/file_reader.py
  - .github/workflows/ci.yml
  - README.md
  - CONTRIBUTING.md
  - SECURITY.md
  - .redteamarena.example.yml
  - tests/unit/test_cli.py
tests:
  - tests/unit/test_cli.py (15 new smoke tests — all passing)
  - tests/ full suite — 111/111 passing
outcome: success
---

## Prompt

Find and complete the remaining things to launch its 0.0.1 as the best opensource, the dev AI world should love it

## Response

Performed a full pre-launch audit via the Explore agent, then executed all critical fixes:

**Version (Task 1):** Bumped `0.1.0` → `0.0.1` in `pyproject.toml`, `cli.py`, and `api_server.py`.

**README (Task 2):** Complete rewrite — replaced all TypeScript/npm/Node.js content with Python/pip equivalents. Added: full CLI reference table with all options, 33-scenario catalog split by Web Security vs AI Safety, Python programmatic API example, GitHub Actions CI/CD integration guide, multi-provider setup docs, config file example.

**CI/CD (Task 3):** Replaced the Node.js/npm matrix with Python 3.10/3.11/3.12 matrix using `setup-python@v5`, `ruff check`, `mypy`, and `pytest`. Added a `publish` job that auto-publishes to PyPI on `v*` tag pushes.

**Docs (Task 4):** Rewrote `CONTRIBUTING.md` for Python workflow (venv, pip, pytest, ruff, mypy). Updated `SECURITY.md` version table to `0.0.x`.

**Config (Task 5):** Created `.redteamarena.example.yml`. Added `ruff>=0.3.0` to dev deps. Added `[tool.ruff]` and `[tool.mypy]` config sections to `pyproject.toml`.

**CLI Tests (Task 6):** Created `tests/unit/test_cli.py` with 15 smoke tests covering version flag, help output for all 7 commands, `list` correctness, and `battle` input validation using Click's `CliRunner`.

**Bug Fix:** Fixed pre-existing bug in `core/file_reader.py` where `read_codebase()` returned `Ok([])` for non-existent directories instead of `Err`. Added `os.path.isdir` guard before walking.

**Test result:** 111/111 passing. Committed as `d13c0d9`.
