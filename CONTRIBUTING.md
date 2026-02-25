# Contributing to RedTeam Arena

Thanks for your interest in contributing! Here's how to get started.

## Development Setup

```bash
# Fork and clone
git clone https://github.com/<your-username>/redteam-arena.git
cd redteam-arena

# Install dependencies
npm install

# Build
npm run build

# Run tests
npm test
```

## Development Commands

| Command | Description |
|---------|-------------|
| `npm run build` | Compile TypeScript and copy scenario files |
| `npm run dev` | Run CLI directly via tsx (no build needed) |
| `npm test` | Run all tests (vitest) |
| `npm run test:watch` | Run tests in watch mode |
| `npm run lint` | Lint source files (eslint) |
| `npm run typecheck` | Type-check without emitting |

## Project Structure

```
src/
├── agents/          # Red and Blue agent implementations
│   ├── red-agent.ts
│   ├── blue-agent.ts
│   ├── claude-adapter.ts
│   └── response-parser.ts
├── core/            # Battle engine and event system
│   ├── battle-engine.ts
│   ├── event-system.ts
│   └── file-reader.ts
├── scenarios/       # Scenario loader + built-in scenarios
│   ├── scenario.ts
│   └── builtin/     # Markdown scenario definitions
├── reports/         # Battle report generation
├── cli.ts           # CLI entry point (commander)
├── display.ts       # Terminal output formatting (chalk)
├── index.ts         # Programmatic API exports
└── types.ts         # Shared TypeScript types
```

## How to Add a New Scenario

1. Create a new Markdown file in `src/scenarios/builtin/`:

```markdown
---
name: my-scenario
description: Short description of what this checks
focus_areas:
  - Pattern to look for
  - Another pattern
severity_guidance: >
  Critical: ...
  High: ...
  Medium: ...
  Low: ...
---

## Red Agent Guidance

Instructions for the attacker agent...

## Blue Agent Guidance

Instructions for the defender agent...
```

2. Run `npm run build` to copy it to `dist/`
3. Verify with `npx tsx src/cli.ts list`
4. Add tests for the new scenario

## Pull Request Guidelines

- **One feature per PR** — keep changes focused
- **Tests required** — all new code needs tests
- **Typecheck must pass** — `npm run typecheck` with zero errors
- **No `any` types** — use proper TypeScript types
- **Follow existing patterns** — look at similar code in the codebase
- **Update docs** if you change CLI options or public API

## Branch Naming

- `feat/short-description` — new features
- `fix/short-description` — bug fixes
- `docs/short-description` — documentation only

## Need Help?

Open an issue with the question label, or start a discussion.
