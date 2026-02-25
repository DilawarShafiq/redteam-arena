# Feature Specification: Static Battle Mode

**Feature Branch**: `001-static-battle-mode`
**Created**: 2026-02-25
**Status**: Draft
**Input**: User description: "Point it at a codebase. Watch two AIs fight over your security. Get a report."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Run a Security Battle (Priority: P1)

A developer points RedTeam Arena at their codebase with a single CLI command and watches two AI agents debate the security of their code in real-time. The Red agent reads source files and identifies vulnerabilities. The Blue agent analyzes each finding and proposes mitigations. The developer sees the entire exchange streamed to their terminal, then receives a summary report.

**Why this priority**: This is the entire product. Without a working battle loop, nothing else matters. It delivers the core "wow" moment — two AIs arguing about your code live.

**Independent Test**: Can be fully tested by running `redteam-arena battle ./test-project --scenario secrets-exposure` against a sample project with known vulnerabilities and confirming the output contains Red findings and Blue mitigations.

**Acceptance Scenarios**:

1. **Given** a valid project directory and a valid scenario name, **When** the user runs `redteam-arena battle ./project --scenario sql-injection`, **Then** the battle starts, Red and Blue agents alternate turns, and the terminal displays each agent's output in real-time with color-coded formatting.
2. **Given** a battle in progress, **When** the Red agent identifies a vulnerability, **Then** the output includes the file path, line reference, vulnerability description, attack vector, and severity rating (Critical/High/Medium/Low).
3. **Given** a Red agent finding, **When** the Blue agent responds, **Then** the output includes an acknowledgment of the finding, a proposed mitigation with concrete code-level guidance, and a confidence assessment.
4. **Given** a battle that has completed all rounds, **When** the battle ends, **Then** a summary is printed to the terminal showing total rounds, vulnerability counts by severity, and mitigation coverage, and a full Markdown report is saved to disk.

---

### User Story 2 - Choose a Scenario (Priority: P2)

A developer selects from built-in attack scenarios to focus the battle on a specific vulnerability class (SQL injection, XSS, auth bypass, secrets exposure) or runs a full audit that covers all categories sequentially.

**Why this priority**: Scenarios give users control over what gets tested. Without them, the battle is unfocused. They also make the tool feel professional and curated.

**Independent Test**: Can be tested by running `redteam-arena battle ./project --scenario xss` and verifying the Red agent focuses exclusively on XSS-related vulnerabilities, then running `--scenario full-audit` and verifying all categories are covered.

**Acceptance Scenarios**:

1. **Given** the built-in scenarios list, **When** the user runs `redteam-arena battle ./project --scenario sql-injection`, **Then** the Red agent focuses its analysis on SQL injection attack vectors only.
2. **Given** the `full-audit` scenario, **When** the user runs it, **Then** each built-in scenario category runs sequentially and the final report aggregates all findings.
3. **Given** an invalid scenario name, **When** the user runs the command, **Then** the system displays an error listing available scenarios and exits with a non-zero code.

---

### User Story 3 - View the Battle Report (Priority: P2)

After a battle completes, the developer gets a detailed Markdown report saved to disk containing all findings, mitigations, severity breakdown, and actionable next steps — ready to share with their team or paste into a PR.

**Why this priority**: The report is the deliverable. The terminal show is the hook, but the report is what developers actually use to fix their code. It needs to be good enough to share without editing.

**Independent Test**: Can be tested by running a battle and verifying the generated `.md` file contains all required sections, parses as valid Markdown, and includes accurate data matching the terminal output.

**Acceptance Scenarios**:

1. **Given** a completed battle, **When** the report is generated, **Then** it is saved as a Markdown file in the current directory with a unique filename (e.g., `redteam-report-<id>.md`).
2. **Given** a generated report, **When** opened, **Then** it contains: battle metadata (date, scenario, target directory), a findings table with severity/file/description, proposed mitigations for each finding, and a summary with counts.
3. **Given** multiple battles run in the same directory, **When** reports are generated, **Then** each has a unique filename and does not overwrite previous reports.

---

### User Story 4 - List Available Scenarios (Priority: P3)

A developer runs `redteam-arena list` to see all available built-in scenarios with their names and descriptions before deciding which one to use.

**Why this priority**: Quality-of-life feature. Users need discoverability, but it's not required for the core battle flow.

**Independent Test**: Can be tested by running `redteam-arena list` and verifying it outputs a formatted table of scenario names and descriptions.

**Acceptance Scenarios**:

1. **Given** the CLI is installed, **When** the user runs `redteam-arena list`, **Then** a formatted list of all built-in scenarios is displayed with name and one-line description.

---

### User Story 5 - Bring Your Own API Key (Priority: P1)

A developer provides their own LLM API key via environment variable to power the Red and Blue agents. The system validates the key is present before starting a battle.

**Why this priority**: Without an API key, no agents can run. This is a hard prerequisite for every battle. Ranked P1 because it gates the entire experience.

**Independent Test**: Can be tested by unsetting `ANTHROPIC_API_KEY` and running a battle, verifying a clear error message appears. Then setting the key and verifying the battle starts.

**Acceptance Scenarios**:

1. **Given** `ANTHROPIC_API_KEY` is set in the environment, **When** a battle starts, **Then** both agents use the Claude API through the configured key.
2. **Given** no API key is set, **When** the user runs a battle command, **Then** the system displays a clear error message explaining which environment variable to set and exits with a non-zero code.
3. **Given** an invalid API key, **When** the first API call fails, **Then** the system displays a clear authentication error and stops the battle gracefully.

---

### Edge Cases

- What happens when the target directory contains no source files? The system displays a clear error: "No source files found in <path>" and exits.
- What happens when the target directory does not exist? The system displays "Directory not found: <path>" and exits with a non-zero code.
- What happens when the LLM provider returns an error mid-battle? The battle stops gracefully, displays the error, saves a partial report with findings collected so far, and exits with a non-zero code.
- What happens when a battle has zero findings? The report indicates "No vulnerabilities found" and the terminal shows a clean result.
- What happens when the codebase is very large? The system limits the number of files analyzed per round and informs the user of the scope boundary.
- What happens when the user presses Ctrl+C during a battle? The battle terminates gracefully, displays a "Battle interrupted" message, and saves a partial report if any findings were collected.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept a target directory path and a scenario name as CLI arguments to start a battle.
- **FR-002**: System MUST read source files from the target directory without modifying them (read-only access).
- **FR-003**: System MUST alternate between Red agent (attacker) and Blue agent (defender) turns for a configurable number of rounds (default: 5 rounds).
- **FR-004**: Red agent MUST analyze source code and produce structured findings containing: file path, line reference, vulnerability description, attack vector, and severity (Critical/High/Medium/Low).
- **FR-005**: Blue agent MUST respond to each Red finding with: acknowledgment, proposed mitigation with code-level guidance, and a confidence level.
- **FR-006**: System MUST stream agent output to the terminal in real-time with color-coded formatting (red for attacker, blue for defender).
- **FR-007**: System MUST generate a Markdown battle report saved to the current working directory upon battle completion.
- **FR-008**: System MUST ship with 5 built-in scenarios: `sql-injection`, `xss`, `auth-bypass`, `secrets-exposure`, and `full-audit`.
- **FR-009**: System MUST validate that a supported LLM API key is present before starting a battle, with a clear error message if missing.
- **FR-010**: System MUST provide a `list` command showing all available scenarios with names and descriptions.
- **FR-011**: System MUST track battle state as a sequence of typed events (attack, defend, round-start, round-end, battle-start, battle-end).
- **FR-012**: System MUST handle interruptions (Ctrl+C) gracefully, saving a partial report when findings exist.
- **FR-013**: System MUST validate the target directory exists and contains source files before starting a battle.
- **FR-014**: Scenarios MUST be defined as Markdown files with structured frontmatter containing: name, description, focus areas, and severity guidance.

### Key Entities

- **Battle**: A complete session of Red vs Blue agent interaction. Contains rounds, events, findings, mitigations, and produces a report. Identified by a unique ID.
- **Round**: A single Red attack + Blue defense exchange. Part of a Battle. Has a sequence number.
- **Finding**: A vulnerability discovered by the Red agent. Contains file path, line reference, description, attack vector, and severity. Belongs to a Round.
- **Mitigation**: A defense response from the Blue agent. Contains acknowledgment, proposed fix, and confidence. Linked to a Finding.
- **Scenario**: A declarative definition of what the Red agent should focus on. Contains name, description, focus areas, prompt guidance. Loaded from Markdown files.
- **Event**: A timestamped, typed record of any action during a battle (agent output, round transitions, battle lifecycle). The event log is the source of truth for battle state.
- **Agent**: An AI entity (Red or Blue) that analyzes code and produces structured output. Powered by an LLM provider via an adapter.
- **Provider**: An LLM service adapter that translates the agent interface into provider-specific API calls. First provider: Claude (Anthropic SDK).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with zero prior experience can install and run their first battle in under 3 minutes (including API key setup).
- **SC-002**: Every battle produces a report containing all findings discovered during the session with zero data loss between terminal output and report.
- **SC-003**: The Red agent identifies at least one real vulnerability in 90% of battles run against codebases with known security issues.
- **SC-004**: The Blue agent provides a relevant, actionable mitigation for 80% of Red agent findings.
- **SC-005**: Battle output streams to the terminal within 2 seconds of the first agent response (no buffering delay).
- **SC-006**: The tool runs on macOS, Linux, and Windows with Node.js 18+ without platform-specific configuration.
- **SC-007**: Users can complete a full battle (5 rounds) within 5 minutes for a typical project (< 50 source files).
- **SC-008**: 80% of developers who see the terminal output understand what is happening without reading documentation.

## Assumptions

- Users have Node.js 18+ installed.
- Users can obtain their own Anthropic API key (BYOK model).
- Claude is the first and default LLM provider; additional providers are out of scope for this feature.
- Static analysis only — no code execution, no Docker, no sandboxing required for v1.
- The Red agent reads code but does not execute it; safety comes from read-only access.
- The default round count of 5 is sufficient for a meaningful battle without excessive API costs.
- Source files are identified by common extensions (.ts, .js, .py, .java, .go, .rb, .php, .cs, .rs, etc.).
- Scenarios are curated by the project team; user-defined custom scenarios are out of scope for this feature.

## Scope Boundaries

### In Scope
- CLI with `battle` and `list` commands
- Red agent (static code analysis for vulnerabilities)
- Blue agent (mitigation proposals)
- 5 built-in scenarios
- Real-time terminal display with color coding
- Markdown battle reports
- Claude as the LLM provider
- Event-sourced battle state
- Graceful error handling and interruption

### Out of Scope
- Code execution or dynamic analysis
- Docker/VM sandboxing
- Multiple concurrent battles
- Web UI or dashboard
- Custom user-defined scenarios
- OpenAI/Gemini/other providers (future feature)
- Plugin system (future feature)
- CI/CD integration
- Historical battle comparison
- Auto-fix / code modification
