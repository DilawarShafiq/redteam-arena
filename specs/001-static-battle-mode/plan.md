# Implementation Plan: Static Battle Mode

**Branch**: `001-static-battle-mode` | **Date**: 2026-02-25 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-static-battle-mode/spec.md`

## Summary

Build a CLI tool that runs static-analysis security battles: a Red AI agent reads a codebase and finds vulnerabilities, a Blue AI agent proposes mitigations, they alternate for N rounds, and the user sees the exchange in real-time with a Markdown report saved to disk. One command: `redteam-arena battle ./project --scenario sql-injection`.

## Technical Context

**Language/Version**: TypeScript 5.x (strict mode), Node.js 18+ LTS
**Primary Dependencies**: commander (CLI), chalk (terminal colors), @anthropic-ai/sdk (Claude LLM), nanoid (IDs)
**Storage**: File system only — scenario files read, report files written, no database
**Testing**: Vitest (unit + integration)
**Target Platform**: Cross-platform CLI (macOS, Linux, Windows) via Node.js
**Project Type**: Single project (CLI tool)
**Performance Goals**: < 2s battle init, real-time streaming output (no buffering), < 5 min full battle (5 rounds, < 50 files)
**Constraints**: Read-only codebase access, single API key (BYOK), no code execution
**Scale/Scope**: Single user, single battle at a time, typical project < 50 source files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| 1. Sandboxed Execution | PASS | Static analysis only — read-only file access, no code execution, no network calls beyond LLM API. Sandbox principle satisfied by design. |
| 2. Observable Battles | PASS | FR-011 requires typed event system (attack, defend, round-start, round-end, battle-start, battle-end). All state changes emit events. |
| 3. Scenario-Driven | PASS | FR-014 defines scenarios as Markdown with frontmatter. 5 built-in scenarios ship with the tool. Plain English definitions. |
| 4. Agent-Agnostic | PASS | Provider abstraction (Agent interface + adapter pattern). Claude is first adapter; interface is provider-independent. |
| 5. Ethical by Default | PASS | Read-only analysis, no executable output, no network egress beyond LLM API. Findings are educational (file paths + descriptions), not weaponizable. |
| 6. Extensible Architecture | PASS | Agent interface, provider adapter, scenario loader — all extension points. Core runs without plugins. |

**Gate result: PASS** — No violations. Proceed to Phase 0.

## Project Structure

### Documentation (this feature)

```text
specs/001-static-battle-mode/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── cli-interface.md
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
src/
├── cli.ts                    # CLI entry point (commander)
├── types.ts                  # Core type definitions
├── display.ts                # Terminal output formatting (chalk)
├── core/
│   ├── battle-engine.ts      # Battle loop: rounds, agent turns, state
│   └── event-system.ts       # Typed event emitter + event log
├── agents/
│   ├── agent.ts              # Agent interface definition
│   ├── red-agent.ts          # Red agent: vulnerability prompts
│   ├── blue-agent.ts         # Blue agent: mitigation prompts
│   ├── provider.ts           # LLM provider interface
│   └── claude-adapter.ts     # Claude SDK adapter (streaming)
├── scenarios/
│   ├── scenario.ts           # Scenario type + loader
│   └── builtin/              # Built-in scenario Markdown files
│       ├── sql-injection.md
│       ├── xss.md
│       ├── auth-bypass.md
│       ├── secrets-exposure.md
│       └── full-audit.md
└── reports/
    └── battle-report.ts      # Markdown report generator

tests/
├── unit/
│   ├── battle-engine.test.ts
│   ├── event-system.test.ts
│   ├── red-agent.test.ts
│   ├── blue-agent.test.ts
│   ├── scenario.test.ts
│   ├── display.test.ts
│   └── battle-report.test.ts
└── integration/
    └── battle-flow.test.ts
```

**Structure Decision**: Single project layout matching the constitution's canonical structure. CLI entry at `src/cli.ts` compiles to `dist/cli.js` (package.json `bin` entry). All modules under `src/` with domain-based subdirectories (core, agents, scenarios, reports).

## Key Design Decisions

### 1. Battle Loop Architecture

The battle engine runs a synchronous loop of rounds. Each round:
1. Red agent receives: scenario context + codebase files + previous findings
2. Red agent streams response → parsed into structured Finding(s)
3. Blue agent receives: Red's findings + original code context
4. Blue agent streams response → parsed into structured Mitigation(s)
5. Events emitted at each step (round-start, attack, defend, round-end)

The loop is `async` but sequential — no parallel agent calls. This keeps the terminal output readable and the event log ordered.

### 2. Streaming + Structured Output

Agents stream raw text to the terminal for the "live battle" effect. After each agent turn completes, the full response is parsed into structured data (Finding/Mitigation). This dual approach gives:
- Real-time terminal experience (streamed chunks via `@anthropic-ai/sdk` stream API)
- Structured data for reports and event log (post-hoc parse of complete response)

### 3. Codebase Reading Strategy

For the target directory:
1. Walk the directory tree, filtering by known source extensions
2. Skip common noise: `node_modules/`, `.git/`, `dist/`, `build/`, `vendor/`, lock files
3. Read file contents up to a size limit (64KB per file) to stay within LLM context
4. Bundle files into a single context string with file-path headers
5. If total content exceeds context budget, prioritize files by scenario relevance (e.g., SQL-related files for sql-injection scenario)

### 4. Scenario Frontmatter Schema

```yaml
---
name: sql-injection
description: Find SQL injection vectors in database queries
focus_areas:
  - Raw SQL string concatenation
  - Unsanitized user input in queries
  - Missing parameterized queries
  - ORM misuse with raw queries
severity_guidance: >
  Critical: Direct user input in SQL without any sanitization.
  High: Indirect user input reaching SQL with partial sanitization.
  Medium: Potential injection via complex data flow.
  Low: Theoretical injection requiring unlikely conditions.
---

## Red Agent Guidance

You are a security researcher analyzing code for SQL injection...

## Blue Agent Guidance

You are a security engineer proposing mitigations for SQL injection...
```

### 5. LLM Provider Abstraction

```
Agent interface → Provider interface → Claude Adapter
```

- `Agent` defines `analyze(context): AsyncIterable<string>` for streaming
- `Provider` defines `stream(messages, options): AsyncIterable<string>`
- `ClaudeAdapter` implements `Provider` using `@anthropic-ai/sdk`
- Agents compose a Provider, not extend it (dependency injection)

### 6. Error Handling Strategy

- Use `Result<T, E>` pattern (discriminated union) for business logic errors
- `throw` only for truly unrecoverable situations (missing dependencies, corrupt state)
- LLM API errors → graceful battle stop + partial report
- File system errors → clear message + exit
- SIGINT handler → graceful shutdown + partial report

## Complexity Tracking

> No constitution violations. No complexity justifications needed.
