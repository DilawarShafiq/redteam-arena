# Quickstart: Static Battle Mode Development

**Feature**: 001-static-battle-mode
**Date**: 2026-02-25

## Prerequisites

- Node.js 18+ (`node --version`)
- npm (`npm --version`)
- Anthropic API key ([console.anthropic.com](https://console.anthropic.com/))

## Setup

```bash
# Clone and install
git clone https://github.com/DilawarShafiq/redteam-arena.git
cd redteam-arena
git checkout 001-static-battle-mode
npm install

# Configure API key
export ANTHROPIC_API_KEY="your-key-here"
```

## Build & Run

```bash
# Build TypeScript
npm run build

# Run a battle
node dist/cli.js battle ./my-project --scenario sql-injection

# Or use dev mode (ts-node)
npm run dev -- battle ./my-project --scenario sql-injection

# List scenarios
node dist/cli.js list
```

## Development

```bash
# Run tests
npm test

# Run tests in watch mode
npx vitest --watch

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

## Project Structure

```
src/
├── cli.ts              # CLI entry (Commander)
├── types.ts            # Core types (Finding, Mitigation, Battle, etc.)
├── display.ts          # Terminal formatting (Chalk)
├── core/
│   ├── battle-engine.ts    # Battle loop
│   └── event-system.ts     # Typed events
├── agents/
│   ├── agent.ts            # Agent interface
│   ├── red-agent.ts        # Red (attacker)
│   ├── blue-agent.ts       # Blue (defender)
│   ├── provider.ts         # LLM provider interface
│   └── claude-adapter.ts   # Claude SDK adapter
├── scenarios/
│   ├── scenario.ts         # Scenario loader
│   └── builtin/            # .md scenario files
└── reports/
    └── battle-report.ts    # Report generator
```

## Key Dependencies

| Package | Purpose |
|---------|---------|
| commander | CLI framework |
| chalk | Terminal colors |
| @anthropic-ai/sdk | Claude LLM API |
| nanoid | Battle/finding ID generation |
| js-yaml | Scenario frontmatter parsing |
| vitest | Testing |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| ANTHROPIC_API_KEY | Yes | Your Anthropic API key |
