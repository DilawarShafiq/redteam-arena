---
id: 012
title: Safe --auto-fix, working SARIF, configurable scan budget
stage: green
date: 2026-07-21
surface: agent
model: claude-opus-4-8
feature: none
branch: main
user: DilawarGopang
command: (conversational)
labels: ["auto-fix", "sarif", "scan-budget", "correctness"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - redteam_arena/core/auto_fix.py
  - redteam_arena/reports/sarif_reporter.py
  - redteam_arena/core/file_reader.py
  - redteam_arena/core/battle_engine.py
  - redteam_arena/core/config.py
  - redteam_arena/cli.py
  - redteam_arena/types.py
  - tests/unit/test_auto_fix.py
  - tests/unit/test_sarif_reporter.py
  - tests/unit/test_scan_budget.py
tests:
  - pytest tests/ (206 passed)
  - ruff + mypy clean
---

## Prompt

complete all open (fix the remaining audit items: --auto-fix, SARIF, the 100KB
scan ceiling).

## Response snapshot

(1) `--auto-fix`: it claimed to apply fixes but wrote markdown, made a branch per
finding, and left the repo on a stray branch — and NO git call's exit code was
checked, so a failed `checkout -b` could commit to main. Rewrote: writing
proposals is the default (no git); branch commits opt-in via `--auto-fix-branch`;
every git call checked; base branch restored in a finally; refuses dirty tree /
non-repo. (2) SARIF: rule IDs were MD5 of prose and fingerprints hashed the
description (churned every run); `%SRCROOT%` malformed; paths relative to scan
dir. Now stable `redteam-arena/<scenario>` IDs, location-based fingerprints,
repo-root-relative paths. (3) Scan budget: added `--max-scan-kb`/`maxScanKb`
(single pass, no cost multiplier) — chose this over multi-pass chunking to avoid
surprise BYOK bills. Surfaced a latent bug: `get_battle()` dropped `scan_scope`.

## Outcome

- ✅ Impact: auto-fix safe; SARIF usable in GitHub code scanning; coverage adjustable
- 🧪 Tests: 174 → 206 passed (auto_fix + sarif + scan_budget suites, all previously 0% covered)
- 📁 Files: auto_fix, sarif_reporter, file_reader, battle_engine, config, cli, types + 3 test files
- 🔁 Next prompts: release 0.0.6, verify pip install
- 🧠 Reflection: surfaced a real cost decision (multi-pass) via AskUserQuestion rather than guessing

## Evaluation notes (flywheel)

- Failure modes observed: none; regression test proves a failed checkout can't move base HEAD
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): default to opt-in for anything that mutates a user's repo or bill
