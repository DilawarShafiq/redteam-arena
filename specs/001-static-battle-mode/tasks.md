# Tasks: Static Battle Mode

**Input**: Design documents from `/specs/001-static-battle-mode/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/cli-interface.md

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, TypeScript/ESM configuration

- [ ] T001 Create directory structure: `src/core/`, `src/agents/`, `src/scenarios/builtin/`, `src/reports/`, `tests/unit/`, `tests/integration/`
- [ ] T002 Configure TypeScript with strict ESM: create `tsconfig.json` (module: NodeNext, moduleResolution: NodeNext, target: ES2022, strict: true, outDir: dist, rootDir: src) and set `"type": "module"` in `package.json`
- [ ] T003 Install dependencies: `commander`, `chalk`, `@anthropic-ai/sdk`, `nanoid`, `js-yaml` as production deps; `vitest`, `@types/js-yaml`, `typescript`, `eslint` as dev deps
- [ ] T004 [P] Configure ESLint for strict TypeScript in `eslint.config.js`
- [ ] T005 [P] Add shebang line `#!/usr/bin/env node` to `src/cli.ts` entry point scaffold and verify `package.json` bin entry maps `redteam-arena` to `dist/cli.js`

**Checkpoint**: Project compiles (`npm run build`) and `node dist/cli.js --help` runs without error

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core types, interfaces, and infrastructure that ALL user stories depend on

- [ ] T006 Define all core types in `src/types.ts`: Severity enum, Finding, Mitigation, Round, BattleConfig, Battle, BattleStatus, BattleEvent discriminated union (battle-start, round-start, attack, defend, round-end, battle-end, error), FileEntry, AgentContext, StreamOptions — per data-model.md
- [ ] T007 [P] Implement typed event system in `src/core/event-system.ts`: typed EventEmitter wrapper with in-memory event log array, emit/on/getLog methods, BattleEvent discriminated union support
- [ ] T008 [P] Define Provider interface in `src/agents/provider.ts`: `stream(messages, options): AsyncIterable<string>` — per contracts/cli-interface.md
- [ ] T009 [P] Define Agent interface in `src/agents/agent.ts`: `analyze(context: AgentContext): AsyncIterable<string>` — per contracts/cli-interface.md
- [ ] T010 [P] Implement scenario type and Markdown frontmatter loader in `src/scenarios/scenario.ts`: parse YAML frontmatter (name, description, focus_areas, severity_guidance) + body sections (redGuidance, blueGuidance) using `js-yaml` with `---` delimiter split — per research.md R4
- [ ] T011 [P] Implement codebase file reader in `src/core/file-reader.ts`: recursive directory walk with extension filter (.ts, .js, .py, .java, .go, .rb, .php, .cs, .rs, etc.), directory exclusions (node_modules, .git, dist, build, vendor), 64KB per-file size cap, 100KB total context budget — per plan.md design decision #3
- [ ] T012 Implement Claude adapter in `src/agents/claude-adapter.ts`: implement Provider interface using `@anthropic-ai/sdk` streaming API (`messages.stream().on('text', cb)`), read `ANTHROPIC_API_KEY` from env, expose `async *stream()` yielding text chunks — per research.md R3

**Checkpoint**: All interfaces defined, `tsc --noEmit` passes, event system and file reader can be unit tested independently

---

## Phase 3: User Story 1 + User Story 5 — Run a Security Battle + BYOK API Key (Priority: P1) — MVP

**Goal**: A developer runs `redteam-arena battle ./project --scenario <name>` and watches Red/Blue agents argue about code security in real-time. API key is validated before battle starts.

**Independent Test**: Run `redteam-arena battle ./test-project --scenario secrets-exposure` with `ANTHROPIC_API_KEY` set. Verify streamed Red findings and Blue mitigations appear in terminal. Unset the key and verify clear error message.

### Implementation for User Story 1 + 5

- [ ] T013 [P] [US1] Implement Red agent in `src/agents/red-agent.ts`: compose Provider, build system prompt from scenario.redGuidance + codebase files, parse streamed response into Finding[] after completion (extract JSON blocks from natural language), implement Agent interface
- [ ] T014 [P] [US1] Implement Blue agent in `src/agents/blue-agent.ts`: compose Provider, build system prompt from scenario.blueGuidance + current findings, parse streamed response into Mitigation[] after completion, implement Agent interface
- [ ] T015 [US1] Implement response parser utility in `src/agents/response-parser.ts`: extract structured JSON blocks (```json ... ```) from streamed agent output, parse into Finding[] or Mitigation[] with validation, return Result<T, ParseError> — per plan.md design decision #2
- [ ] T016 [US1] Implement battle engine in `src/core/battle-engine.ts`: async battle loop (N rounds), each round: emit round-start → Red agent analyze → parse findings → emit attack → Blue agent analyze → parse mitigations → emit defend → emit round-end. Track Battle state (pending→running→completed/interrupted/error). Compose event system, agents, file reader. — per plan.md design decision #1
- [ ] T017 [US1] Implement terminal display in `src/display.ts`: chalk-based formatters for battle header (version, scenario, target), Red findings (red text with file:line, severity, attack vector), Blue mitigations (blue text with fix, confidence), round separators, battle summary (counts by severity, mitigation coverage), report path. Stream-friendly: accept chunks for real-time display. — per spec.md acceptance scenarios
- [ ] T018 [US1] [US5] Implement CLI entry with battle command and API key validation in `src/cli.ts`: Commander program with `battle <directory>` command, `--scenario` required option, `--rounds` optional (default 5). Pre-flight checks: validate ANTHROPIC_API_KEY exists (clear error if missing), validate directory exists and has source files (FR-013), validate scenario name. Wire up battle engine → display → report. SIGINT handler stub.

**Checkpoint**: `redteam-arena battle ./test-project --scenario secrets-exposure` runs a full battle with streaming terminal output. Missing API key shows clear error.

---

## Phase 4: User Story 2 — Choose a Scenario (Priority: P2)

**Goal**: Red agent behavior changes based on the selected scenario. Five built-in scenarios ship with the tool. Invalid scenario names produce helpful errors.

**Independent Test**: Run with `--scenario sql-injection` and verify Red focuses on SQL vectors. Run with `--scenario invalid` and verify error lists available scenarios.

### Implementation for User Story 2

- [ ] T019 [P] [US2] Create `sql-injection` scenario in `src/scenarios/builtin/sql-injection.md`: frontmatter (name, description, focus_areas for raw SQL concatenation/unsanitized input/missing parameterized queries/ORM misuse, severity_guidance), Red guidance section, Blue guidance section — per plan.md scenario schema
- [ ] T020 [P] [US2] Create `xss` scenario in `src/scenarios/builtin/xss.md`: focus on innerHTML/dangerouslySetInnerHTML/unescaped template interpolation/DOM manipulation with user input, severity guidance for reflected vs stored vs DOM-based XSS
- [ ] T021 [P] [US2] Create `auth-bypass` scenario in `src/scenarios/builtin/auth-bypass.md`: focus on missing auth checks/broken access control/insecure session handling/privilege escalation/IDOR
- [ ] T022 [P] [US2] Create `secrets-exposure` scenario in `src/scenarios/builtin/secrets-exposure.md`: focus on hardcoded API keys/passwords/tokens/connection strings, .env files in repo, secrets in logs
- [ ] T023 [US2] Create `full-audit` meta-scenario in `src/scenarios/builtin/full-audit.md`: frontmatter marks it as meta-scenario, battle engine runs sql-injection → xss → auth-bypass → secrets-exposure sequentially, aggregates all findings into single report
- [ ] T024 [US2] Add scenario validation to CLI: on invalid scenario name, display error listing all available scenarios with descriptions (from scenario loader) and exit code 2 — per contracts/cli-interface.md error messages

**Checkpoint**: Each scenario produces focused Red agent output. `full-audit` runs all four sequentially. Invalid name shows helpful error.

---

## Phase 5: User Story 3 — View the Battle Report (Priority: P2)

**Goal**: Every completed battle saves a detailed Markdown report to disk with findings, mitigations, severity breakdown, and battle metadata.

**Independent Test**: Run a battle and verify `redteam-report-<id>.md` is created in the current directory with all required sections.

### Implementation for User Story 3

- [ ] T025 [US3] Implement battle report generator in `src/reports/battle-report.ts`: generate Markdown from Battle object — header (title, date, scenario, target), summary table (rounds, findings by severity, mitigation coverage), findings detail (one section per finding with severity badge, file:line, description, attack vector, Blue's mitigation), collapsible raw battle log. Use nanoid for unique report filename `redteam-report-<id>.md`. — per contracts/cli-interface.md report output contract
- [ ] T026 [US3] Integrate report generation into battle engine completion flow in `src/core/battle-engine.ts`: on battle-end event, call report generator, write to cwd, display report path in terminal. On partial completion (error/interrupt), still generate report with collected findings.

**Checkpoint**: Battle produces `redteam-report-<id>.md` with all sections. Multiple battles produce unique filenames. Partial battles save partial reports.

---

## Phase 6: User Story 4 — List Available Scenarios (Priority: P3)

**Goal**: `redteam-arena list` shows all built-in scenarios with names and descriptions.

**Independent Test**: Run `redteam-arena list` and verify formatted table output.

### Implementation for User Story 4

- [ ] T027 [US4] Add `list` command to CLI in `src/cli.ts`: load all scenarios via scenario loader, display formatted table (name + description) with usage hint, exit code 0 — per contracts/cli-interface.md list command output

**Checkpoint**: `redteam-arena list` displays all 5 scenarios with descriptions.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Error handling, graceful shutdown, edge cases, and testing

- [ ] T028 Implement graceful SIGINT handling in `src/cli.ts`: listen for SIGINT, set battle status to "interrupted", emit battle-end event, save partial report if findings exist, display "Battle interrupted" message — per FR-012
- [ ] T029 Implement edge case handling across CLI and battle engine: empty directory (no source files → clear error), non-existent directory (→ clear error), zero findings (→ "No vulnerabilities found" in report), large codebase (→ file count/size limits with user notification) — per spec.md edge cases
- [ ] T030 [P] Write unit tests in `tests/unit/event-system.test.ts`: event emission, log accumulation, typed event discrimination
- [ ] T031 [P] Write unit tests in `tests/unit/scenario.test.ts`: frontmatter parsing, scenario loading, invalid scenario handling
- [ ] T032 [P] Write unit tests in `tests/unit/file-reader.test.ts`: extension filtering, directory exclusions, size caps
- [ ] T033 [P] Write unit tests in `tests/unit/battle-report.test.ts`: Markdown generation from Battle object, partial report with zero mitigations
- [ ] T034 [P] Write unit tests in `tests/unit/response-parser.test.ts`: JSON block extraction, malformed response handling, Result error cases
- [ ] T035 Write integration test in `tests/integration/battle-flow.test.ts`: mock Claude adapter, run full battle flow with fixture files, verify events emitted in order, verify report generated
- [ ] T036 Run quickstart.md validation: follow quickstart.md steps on clean checkout, verify build + battle + list commands work end-to-end

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **US1+US5 (Phase 3)**: Depends on Phase 2 — MVP delivery
- **US2 (Phase 4)**: Depends on Phase 2 (scenario loader). Can run in parallel with Phase 3 if team capacity allows, but Phase 3 provides the battle engine that uses scenarios.
- **US3 (Phase 5)**: Depends on Phase 3 (battle engine produces Battle object for reports)
- **US4 (Phase 6)**: Depends on Phase 2 (scenario loader) — can run in parallel with Phases 3-5
- **Polish (Phase 7)**: Depends on Phases 3-6 completion

### User Story Dependencies

- **US1 + US5 (P1)**: After Phase 2 — no dependencies on other stories
- **US2 (P2)**: After Phase 2 — independent of US1 for scenario file creation; scenario validation integrates with CLI from US1
- **US3 (P2)**: After US1 — needs Battle object from battle engine
- **US4 (P3)**: After Phase 2 — independent, only needs scenario loader

### Within Each User Story

- Models/types before services
- Services before CLI integration
- Core implementation before polish
- Story complete before checkpoint validation

### Parallel Opportunities

- T004 + T005: ESLint config and CLI scaffold (different files)
- T007 + T008 + T009 + T010 + T011: Event system, provider interface, agent interface, scenario loader, file reader (all independent modules)
- T013 + T014: Red agent and Blue agent (independent implementations of same interface)
- T019 + T020 + T021 + T022: All four scenario files (independent Markdown files)
- T030 + T031 + T032 + T033 + T034: All unit tests (independent test files)

---

## Parallel Example: Phase 2 Foundational

```bash
# Launch all independent foundational modules together:
Task: "Implement typed event system in src/core/event-system.ts"
Task: "Define Provider interface in src/agents/provider.ts"
Task: "Define Agent interface in src/agents/agent.ts"
Task: "Implement scenario loader in src/scenarios/scenario.ts"
Task: "Implement file reader in src/core/file-reader.ts"
```

## Parallel Example: User Story 1

```bash
# Launch Red and Blue agents together:
Task: "Implement Red agent in src/agents/red-agent.ts"
Task: "Implement Blue agent in src/agents/blue-agent.ts"
```

## Parallel Example: User Story 2

```bash
# Launch all scenario files together:
Task: "Create sql-injection scenario in src/scenarios/builtin/sql-injection.md"
Task: "Create xss scenario in src/scenarios/builtin/xss.md"
Task: "Create auth-bypass scenario in src/scenarios/builtin/auth-bypass.md"
Task: "Create secrets-exposure scenario in src/scenarios/builtin/secrets-exposure.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 + 5 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: US1 + US5 (Run Battle + BYOK)
4. **STOP and VALIDATE**: `redteam-arena battle ./test-project --scenario secrets-exposure` works end-to-end
5. Ship v0.1.0-alpha if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 + US5 → Test independently → **MVP!**
3. Add US2 (Scenarios) → All 5 scenarios work → Ship v0.1.0-beta
4. Add US3 (Reports) → Markdown reports generated → Ship v0.1.0-rc
5. Add US4 (List) → `list` command works → Ship v0.1.0
6. Polish → Tests, edge cases, graceful shutdown → Ship v0.1.0 final

---

## Notes

- [P] tasks = different files, no dependencies between them
- [Story] label maps task to specific user story for traceability
- Total tasks: 36
- Tasks per story: US1+US5: 6, US2: 6, US3: 2, US4: 1
- Setup: 5, Foundational: 7, Polish: 9
- Parallel opportunities: 5 groups identified
- Suggested MVP scope: Phase 1 + Phase 2 + Phase 3 (T001–T018)
