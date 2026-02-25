---
id: 002
title: Static Battle Mode Specification
stage: spec
date: 2026-02-25
surface: agent
model: claude-opus-4-6
feature: 001-static-battle-mode
branch: 001-static-battle-mode
user: DilawarShafiq
command: /sp.specify
labels: ["spec", "static-battle-mode", "mvp", "cli", "red-agent", "blue-agent"]
links:
  spec: specs/001-static-battle-mode/spec.md
  ticket: null
  adr: null
  pr: null
files:
  - specs/001-static-battle-mode/spec.md
  - specs/001-static-battle-mode/checklists/requirements.md
  - history/prompts/001-static-battle-mode/002-static-battle-mode-specification.spec.prompt.md
tests:
  - none
---

## Prompt

Here's my vision for RedTeam Arena feature #1:

The MVP

"Point it at a codebase. Watch two AIs fight over your security. Get a report."

redteam-arena battle ./my-project --scenario sql-injection

That's it. One command. Red agent attacks, Blue agent defends, you watch the war in your terminal.

Feature #1: Static Battle Mode

Skip the sandbox entirely for v1. No Docker, no VMs, no execution. Static analysis battles only — the Red agent reads your code and finds vulnerabilities, the Blue agent proposes mitigations, and they go back and forth. This is:

- 10x simpler to build
- Still visually stunning (two AIs arguing about your code in real-time)
- Inherently safe (no code execution = no sandbox escape possible)
- The part people will screenshot and share

How It Works:
- Red agent reads code, finds vulnerabilities (file path, line, severity, attack vector)
- Blue agent proposes mitigations (acknowledgment, fix, confidence)
- Real-time terminal display with color coding
- Battle report saved as Markdown

Architecture: CLI (Commander), battle engine, event system, agent interface, Red/Blue agents, Claude adapter, scenario loader, built-in scenarios (sql-injection, xss, auth-bypass, secrets-exposure, full-audit), report generator, terminal display (Chalk).

Key Decisions: BYOK (user provides API key), Claude as first provider, no sandbox needed (static analysis = read-only), scenarios as Markdown with frontmatter, event-sourced battle state, Commander.js CLI, Chalk terminal styling.

## Response snapshot

Created comprehensive feature specification for Static Battle Mode with:
- 5 user stories (P1: Run Battle, P1: BYOK API Key, P2: Choose Scenario, P2: View Report, P3: List Scenarios)
- 14 functional requirements (FR-001 through FR-014)
- 8 key entities (Battle, Round, Finding, Mitigation, Scenario, Event, Agent, Provider)
- 8 measurable success criteria
- 6 edge cases with defined behavior
- Clear scope boundaries (in/out)
- Zero [NEEDS CLARIFICATION] markers — user vision was detailed enough for complete spec

## Outcome

- Impact: Feature specification created for Static Battle Mode MVP — the foundational feature of RedTeam Arena
- Tests: Spec quality checklist passed (all items checked)
- Files: 2 files created (spec.md, checklists/requirements.md)
- Next prompts: `/sp.clarify` to validate completeness, then `/sp.plan` to architect the implementation
- Reflection: User provided exceptionally detailed vision including architecture, scenarios, and UX mockup. No clarification needed — all gaps filled with reasonable defaults documented in Assumptions section.

## Evaluation notes (flywheel)

- Failure modes observed: None — user input was comprehensive
- Graders run and results (PASS/FAIL): Spec quality checklist PASS (16/16 items)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Run /sp.clarify to stress-test spec completeness with targeted questions
