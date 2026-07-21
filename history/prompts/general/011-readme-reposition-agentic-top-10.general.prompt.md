---
id: 011
title: Reposition README around OWASP Agentic Top 10
stage: explainer
date: 2026-07-21
surface: agent
model: claude-opus-4-8
feature: none
branch: main
user: DilawarGopang
command: (conversational)
labels: ["docs", "positioning", "readme"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - README.md
tests:
  - verified every scenario name referenced in README resolves to a builtin file
---

## Prompt

do whatever is best for opensource project like this (reposition the README /
make the project's real value legible).

## Response snapshot

Rewrote the README to lead with the ASI01–ASI10 mapping (its own table, linked
to the OWASP standard) instead of "AI vs AI adversarial testing" and
"Enterprise-grade auditing for SOC 2 / ISO / HIPAA". Added a "What this is, and
what it isn't" section: no execution, no PoCs, high LLM false-discovery rates,
every finding needs human confirmation; compliance output is preparatory input,
not an audit. Documented the validation + scope-disclosure steps in How It Works.
Showed gemini/ollama alongside openai; dropped "Claude by default". Corrected
"full-audit runs all scenarios" (it declares four). Fixed three scenario names
carrying a stray `.md` suffix that would have failed if passed to `--scenario`.

## Outcome

- ✅ Impact: the differentiator (10/10 ASI coverage) is now legible; claims match behaviour
- 🧪 Tests: scenario-name resolution check passed
- 📁 Files: README.md
- 🔁 Next prompts: fix auto-fix, SARIF, scan budget
- 🧠 Reflection: repositioning was the highest-leverage change for how the project reads

## Evaluation notes (flywheel)

- Failure modes observed: none
- Graders run and results (PASS/FAIL): PASS
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): keep README claims tied to verifiable CLI output
