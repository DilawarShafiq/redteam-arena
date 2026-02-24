<!--
+==================================================================+
|                    SYNC IMPACT REPORT                             |
+==================================================================+
| Constitution Version : 1.0.0                                     |
| Ratified             : 2026-02-24                                |
| Status               : ACTIVE                                    |
| Sync Scope           : All agents, all features, all branches    |
| Breaking Changes     : N/A (initial ratification)                |
| Migration Required   : None                                      |
| Affected Specs       : All future specs inherit these principles  |
| Affected Plans       : All future plans inherit these principles  |
| Affected Tasks       : All future tasks inherit these principles  |
+==================================================================+
-->

# Project Constitution: RedTeam Arena

> Version 1.0.0 — Ratified 2026-02-24

## Project Identity

- **Name**: RedTeam Arena
- **Purpose**: An adversarial AI red team platform where autonomous AI agents attack and defend systems in fully automated security testing battles.
- **Tagline**: "AI vs AI. The ultimate security stress test."
- **License**: MIT
- **Distribution**: npm (`npx redteam-arena`)
- **Repository**: https://github.com/DilawarShafiq/redteam-arena

---

## Core Principles

These six principles are non-negotiable. Every feature, spec, plan, and task MUST uphold all six. Violations are blocking defects.

### 1. Sandboxed Execution

All attack/defense simulations MUST run in isolated sandboxes. No real systems are ever harmed. Every execution environment is ephemeral, network-isolated, and resource-constrained. There are no exceptions — if it cannot be sandboxed, it cannot be built.

- **Invariant**: Zero side effects on production systems, host machines, or external networks.
- **Test**: Every battle run must prove sandbox containment before execution begins.
- **Kill switch**: Any sandbox breach immediately terminates all running agents and halts the battle.

### 2. Observable Battles

Every attack attempt, defense response, and state change MUST be recorded and replayable. Full transparency is mandatory. Battles produce structured event logs, not opaque summaries.

- **Invariant**: No silent state mutations. Every action emits a timestamped, typed event.
- **Test**: Any completed battle can be replayed from its event log and produce identical output.
- **Format**: Events are structured JSON with `timestamp`, `agent`, `action`, `target`, `result` fields.

### 3. Scenario-Driven

Attacks are defined as declarative scenarios in plain English. No scripting is required for basic use. Advanced users may extend scenarios programmatically, but the default path is natural language.

- **Invariant**: Any scenario expressible in the scenario DSL can also be expressed in plain English.
- **Test**: A non-technical user can define and run a basic attack scenario without writing code.
- **Format**: Scenario files are Markdown with structured frontmatter.

### 4. Agent-Agnostic

Red and blue agents can be powered by any LLM provider — Claude, GPT, Gemini, open-source models, or custom implementations. No vendor lock-in.

- **Invariant**: The agent interface is provider-independent. Swapping providers requires only configuration, not code changes.
- **Test**: The same scenario produces valid results with at least two different LLM providers.
- **Contract**: All agents implement the `Agent` interface; provider adapters handle API-specific logic.
### 5. Ethical by Default

Built-in guardrails prevent real-world harm. Attack techniques are educational, never weaponizable against live targets. All output is scoped to the sandbox.

- **Invariant**: No generated payload, exploit, or technique can escape the sandbox or target external systems.
- **Test**: Static analysis and runtime checks validate that no output contains actionable exploits for real-world targets.
- **Guardrails**: Content filters on agent output, network egress blocking, and scope-limitation checks run before every action.

### 6. Extensible Architecture

Plugin system for custom attack vectors, defense strategies, scoring algorithms, and report formats. The core is minimal; capabilities grow through plugins.

- **Invariant**: Core functionality does not depend on any plugin. Plugins depend on core interfaces only.
- **Test**: The platform runs a basic battle with zero plugins installed.
- **Contract**: Plugins implement typed interfaces and register through a discovery mechanism. No monkey-patching.

---

## Tech Stack

| Layer           | Technology                        |
|-----------------|-----------------------------------|
| Language        | TypeScript (strict mode)          |
| Runtime         | Node.js (LTS)                     |
| Module System   | ESM (ECMAScript Modules)          |
| Package Manager | npm                               |
| Testing         | Vitest                            |
| Linting         | ESLint with strict TypeScript rules |
| Formatting      | Prettier                          |
| Build           | tsup or tsc                       |
| CI              | GitHub Actions                    |

---

## Code Quality Standards

### TypeScript

- `strict: true` in `tsconfig.json` — no exceptions.
- No `any` types unless explicitly justified and documented with `// eslint-disable-next-line` and a reason.
- Prefer `unknown` over `any` for external data boundaries.
- All public APIs have JSDoc comments with `@param`, `@returns`, and `@throws`.
- Use discriminated unions over loose string types for state machines and events.

### Testing

- **Framework**: Vitest.
- **Coverage target**: 80% line coverage minimum, 90% for core modules (sandbox, agent interface, scenario engine).
- **Test naming**: `describe("ModuleName", () => { it("should <expected behavior> when <condition>") })`.
- **Test types**: Unit tests for all pure logic. Integration tests for agent-provider interactions. E2E tests for full battle scenarios.
- **No test pollution**: Each test is independent. No shared mutable state between tests.

### Performance

- Battle initialization: < 2 seconds for standard scenarios.
- Event logging: zero-copy where possible; never block the battle loop.
- Memory: agent context windows are bounded; no unbounded accumulation.

### Security

- No secrets in code — `.env` files and environment variables only.
- All user/agent input is sanitized before processing.
- Sandbox escape is treated as a P0 severity bug.
- Dependency audit runs on every CI build.

### Architecture

- **Separation of concerns**: Core (sandbox, events, agents) is independent of UI, CLI, and reporting.
- **Dependency injection**: Agents, providers, and plugins are injected — never imported directly.
- **Event-driven**: Battle state flows through typed events, not imperative mutations.
- **Error handling**: All errors are typed. Use `Result<T, E>` patterns over thrown exceptions for business logic. Reserve `throw` for truly exceptional/unrecoverable situations.
---

## Project Structure (Canonical)

```
redteam-arena/
  src/
    core/           # Sandbox, event system, battle engine
    agents/         # Agent interface, provider adapters
    scenarios/      # Scenario parser, DSL, built-in scenarios
    plugins/        # Plugin loader, plugin interfaces
    reports/        # Report generators (JSON, Markdown, HTML)
    cli/            # CLI entry point and commands
  tests/
    unit/
    integration/
    e2e/
  specs/              # Feature specs, plans, tasks
  history/            # PHRs and ADRs
  .specify/           # SpecKit Plus configuration
  scenarios/          # User-defined scenario files
```

---

## Decision-Making Framework

When facing architectural or implementation choices:

1. **Does it violate a Core Principle?** If yes, it is rejected. No negotiation.
2. **Is it the smallest viable change?** Prefer incremental progress over large rewrites.
3. **Is it reversible?** Prefer reversible decisions. Irreversible decisions require an ADR.
4. **Is it testable?** If it cannot be tested, it cannot be merged.
5. **Does it introduce vendor lock-in?** If yes, abstract behind an interface first.

---

## Glossary

| Term           | Definition                                                                 |
|----------------|----------------------------------------------------------------------------|
| **Red Agent**  | An AI agent that autonomously discovers and exploits vulnerabilities.       |
| **Blue Agent** | An AI agent that detects, responds to, and mitigates attacks in real-time.  |
| **Battle**     | A complete attack/defense simulation session with structured event output.  |
| **Scenario**   | A declarative definition of an attack vector, scope, and success criteria.  |
| **Sandbox**    | An isolated, ephemeral execution environment for running battles safely.    |
| **Event**      | A typed, timestamped record of an agent action or state change.            |
| **Plugin**     | An extension that adds attack vectors, defenses, or report formats.        |
| **Provider**   | An LLM service adapter (Claude, GPT, Gemini, etc.).                       |

---

## Amendment Process

1. Propose a change via PR with rationale.
2. All core principles require unanimous agreement from maintainers.
3. Non-principle changes require one approval.
4. Every amendment increments the constitution version.
5. Amendment history is tracked in `history/adr/`.
