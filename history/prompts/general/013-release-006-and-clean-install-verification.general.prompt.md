---
id: 013
title: Release 0.0.6, verify pip install, fix command name
stage: green
date: 2026-07-21
surface: agent
model: claude-opus-4-8
feature: none
branch: main
user: DilawarGopang
command: (conversational)
labels: ["release", "verification", "docs"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - pyproject.toml
  - redteam_arena/__init__.py
  - CHANGELOG.md
tests:
  - pytest tests/ (206 passed)
  - python -m build + twine check (PASSED)
  - clean venv pip install redteam-arena==0.0.6 (verified)
---

## Prompt

what do you need from me to release all changes so users can pip install redteam
latest version and git shows all updated? did you try pip install our redteam?

## Response snapshot

Confirmed no token needed (Trusted Publishing proven on 0.0.5). Bumped to 0.0.6
in pyproject + __init__, dated the CHANGELOG, verified build + twine check,
committed, tagged v0.0.6, pushed. CI published via OIDC. The `/pypi/.../json`
summary endpoint cache-lagged at 0.0.5, but `/0.0.6/json` returned 200 and
`/simple/` listed the wheel (with a provenance attestation). Then did the real
test the user asked for: clean venv `pip install redteam-arena` → 0.0.6, and ran
the CLI. This caught a docs bug — the console command is `redteam-arena`, NOT
`redteam` (never registered). Swept the repo; two bad refs were in CHANGELOG
(mine), README was already correct; fixed and pushed. Corrected the stale memory
note too.

## Outcome

- ✅ Impact: 0.0.6 live and clean-install-verified; command name corrected everywhere
- 🧪 Tests: 206 passed; clean install + CLI smoke test passed
- 📁 Files: pyproject.toml, __init__.py, CHANGELOG.md
- 🔁 Next prompts: backfill PHRs; save memory for next session
- 🧠 Reflection: only a real pip install (not a local build) surfaces packaging/entry-point bugs

## Evaluation notes (flywheel)

- Failure modes observed: relied on cached PyPI JSON endpoint at first; corrected via /simple/ and version endpoint
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): always clean-install the published artifact after a release, not just twine check
