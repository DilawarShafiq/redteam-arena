---
id: 010
title: OWASP ASI mapping, provider-agnostic models, 0.0.5 release
stage: green
date: 2026-07-21
surface: agent
model: claude-opus-4-8
feature: none
branch: main
user: DilawarGopang
command: (conversational)
labels: ["owasp-agentic", "providers", "release", "ci"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - redteam_arena/scenarios/builtin/*.md (10 agentic scenarios)
  - redteam_arena/scenarios/scenario.py
  - redteam_arena/cli.py
  - redteam_arena/agents/red_agent.py
  - redteam_arena/agents/blue_agent.py
  - redteam_arena/agents/auditor_agent.py
  - redteam_arena/reports/sarif_reporter.py
  - CHANGELOG.md
  - pyproject.toml
  - .github/workflows/ci.yml
  - tests/unit/test_owasp_asi_coverage.py
  - tests/unit/test_provider_agnostic_models.py
tests:
  - pytest tests/ (174 passed)
  - clean pip install of published 0.0.5
---

## Prompt

is 0.0.5 all published now? there should be no Claude model hardcoded, people
should use any llm. Map scenarios to the OWASP Agentic Top 10 and release.

## Response snapshot

Stamped `owasp_asi` frontmatter on the 10 agentic scenarios; `redteam-arena list`
now prints "OWASP Top 10 for Agentic Applications 2026: 10/10 covered". Made
agents provider-agnostic: Red/Blue/Auditor no longer inject a Claude model —
they send an empty model so each adapter applies its own default (gpt-4o,
gemini-2.0-flash, llama3.2, claude-sonnet-4); `--model` forwarded verbatim.
Removed a third hardcoded version string in `cli.py`. Backfilled the missing
0.0.2 CHANGELOG entry (off-by-one) and synced SARIF `semanticVersion`. Switched
CI publish to Trusted Publishing (OIDC, no token) after the pasted PyPI token was
revoked, and added `tags: ['v*']` so tag pushes actually trigger the publish job
(broken since 0.0.1 — all prior releases were manual). Tagged and published 0.0.5.

## Outcome

- ✅ Impact: any LLM usable; ASI coverage visible; first release ever through CI
- 🧪 Tests: 174 passed; clean install verified
- 📁 Files: 10 scenarios, scenario.py, cli.py, 3 agents, sarif_reporter, ci.yml, CHANGELOG, pyproject + 2 test files
- 🔁 Next prompts: complete remaining open items (auto-fix, SARIF, scan budget)
- 🧠 Reflection: the release pipeline had never run — decorative automation is worse than none

## Evaluation notes (flywheel)

- Failure modes observed: refused a pasted PyPI token; switched to Trusted Publishing instead
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): verify secret-free release paths before trusting "automation exists"
