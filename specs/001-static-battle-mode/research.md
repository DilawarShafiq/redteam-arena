# Research: Static Battle Mode

**Feature**: 001-static-battle-mode
**Date**: 2026-02-25

## R1: CLI Framework

- **Decision**: Commander.js v14
- **Rationale**: De facto standard for Node.js CLIs. Mature, well-typed, ESM-compatible. Subcommand support (`battle`, `list`) built-in. Auto-generates help text.
- **Alternatives considered**:
  - `yargs` — heavier, more complex API, less idiomatic for simple CLIs
  - `citty` / `cleye` — newer but smaller ecosystem, less documentation
  - `oclif` — too heavy for a single-binary CLI, designed for plugin-based CLIs

## R2: Terminal Styling

- **Decision**: Chalk v5 (pure ESM)
- **Rationale**: Standard terminal coloring library. v5 is pure ESM (matches project requirement). Supports 256 colors, RGB, and style composition.
- **Alternatives considered**:
  - `picocolors` — smaller but no RGB support, less style composition
  - `kleur` — good but smaller community, fewer style options
  - `ansi-colors` — CJS only, not ESM compatible

## R3: LLM SDK

- **Decision**: @anthropic-ai/sdk (latest)
- **Rationale**: Official Anthropic SDK. Native streaming support via `.messages.stream()` with `on('text', cb)` event API. Auto-reads `ANTHROPIC_API_KEY` from environment. Ships ESM + CJS.
- **Alternatives considered**:
  - Raw HTTP fetch — more work, no streaming helpers, error handling burden
  - `ai` (Vercel AI SDK) — adds unnecessary abstraction for single-provider MVP

## R4: Scenario Frontmatter Parsing

- **Decision**: Custom minimal parser (split on `---` delimiters, parse YAML via `js-yaml`)
- **Rationale**: `gray-matter` is CJS-only (v5 ESM not released). A simple custom parser avoids the `createRequire` hack. Scenario frontmatter is a fixed schema — only needs `name`, `description`, `focus_areas`, `severity_guidance`. `js-yaml` is ESM-compatible and handles the YAML portion.
- **Alternatives considered**:
  - `gray-matter` with `createRequire` — works but ugly, adds CJS dependency to ESM project
  - `vfile-matter` — ESM-native but pulls in the entire vfile ecosystem
  - Manual regex split + JSON — fragile for YAML content

## R5: ID Generation

- **Decision**: nanoid v5 (pure ESM)
- **Rationale**: Lightweight, URL-safe ID generation. Pure ESM. `customAlphabet` allows readable 8-char IDs for battle reports (e.g., `redteam-report-a1b2c3d4.md`).
- **Alternatives considered**:
  - `crypto.randomUUID()` — built-in but UUIDs are long and ugly in filenames
  - `uuid` — heavier, UUID format not needed
  - Timestamp-based — collision risk if two battles start same second

## R6: TypeScript + ESM Configuration

- **Decision**: `module: "NodeNext"`, `moduleResolution: "NodeNext"`, `target: "ES2022"`
- **Rationale**: Forward-compatible ESM configuration for Node.js. Requires `.js` extensions in imports (TypeScript resolves `.ts` at compile time). `ES2022` target gives top-level await, `Array.at()`, and other modern features while maintaining Node 18 compatibility.
- **Key requirement**: `"type": "module"` in `package.json`

## R7: Structured Output Parsing

- **Decision**: Prompt-guided JSON blocks within natural language response
- **Rationale**: Agent responses stream as natural language (for terminal display) but include structured JSON blocks delimited by markers (e.g., ````json ... ```). After streaming completes, parse the JSON blocks to extract typed Finding/Mitigation objects. This gives both real-time display AND structured data without requiring JSON-only mode (which kills the "watching a battle" experience).
- **Alternatives considered**:
  - JSON-only responses — no streaming "battle" feel, just data dumps
  - Two API calls per turn (one stream, one structured) — doubles cost and latency
  - Custom DSL parsing — fragile, hard to maintain

## R8: Event System Architecture

- **Decision**: Typed EventEmitter with in-memory event log array
- **Rationale**: Node.js `EventEmitter` is built-in, familiar, and synchronous (events fire in order). Wrap with typed event map (discriminated union). Maintain a parallel `events: BattleEvent[]` array as the source of truth for replay and reports. No external dependency needed.
- **Alternatives considered**:
  - RxJS — overkill for sequential event flow, massive dependency
  - Custom pub/sub — reinventing EventEmitter for no reason
  - File-based event log — premature persistence, adds I/O complexity

## R9: Codebase File Reading

- **Decision**: Recursive `fs.readdir` with extension filter + size cap + directory exclusions
- **Rationale**: Node.js `fs.readdir({ recursive: true })` (Node 18.17+) handles directory walking natively. Filter by known source extensions. Skip `node_modules`, `.git`, `dist`, `build`, `vendor`, lock files. Cap individual files at 64KB. Cap total context at ~100KB to stay within LLM context window.
- **Alternatives considered**:
  - `glob` library — adds dependency for something `readdir` handles
  - `fast-glob` — overkill, performance not a concern for < 50 files
  - `.gitignore` parsing — nice-to-have but adds complexity; hardcoded exclusions sufficient for MVP
