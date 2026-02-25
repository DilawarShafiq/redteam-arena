# Data Model: Static Battle Mode

**Feature**: 001-static-battle-mode
**Date**: 2026-02-25

## Core Types

### Severity

```
Enum: "critical" | "high" | "medium" | "low"
```

### Finding

A vulnerability discovered by the Red agent during a round.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique finding ID (nanoid) |
| roundNumber | number | Round in which this finding was discovered |
| filePath | string | Relative path to the vulnerable file |
| lineReference | string | Line number or range (e.g., "12" or "12-15") |
| description | string | Human-readable vulnerability description |
| attackVector | string | How the vulnerability could be exploited |
| severity | Severity | Critical / High / Medium / Low |
| codeSnippet | string (optional) | Relevant code excerpt |

### Mitigation

A defense response from the Blue agent linked to a Finding.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique mitigation ID (nanoid) |
| findingId | string | References the Finding being mitigated |
| roundNumber | number | Round in which this mitigation was proposed |
| acknowledgment | string | Blue agent's assessment of the finding |
| proposedFix | string | Concrete code-level mitigation guidance |
| confidence | "high" \| "medium" \| "low" | Blue agent's confidence in the fix |

### Round

A single Red attack + Blue defense exchange.

| Field | Type | Description |
|-------|------|-------------|
| number | number | Sequential round number (1-based) |
| findings | Finding[] | Vulnerabilities found in this round |
| mitigations | Mitigation[] | Defense responses for this round's findings |
| redRawOutput | string | Full streamed text from Red agent |
| blueRawOutput | string | Full streamed text from Blue agent |

### Scenario

A declarative attack focus definition loaded from Markdown.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Scenario identifier (e.g., "sql-injection") |
| description | string | One-line description for listing |
| focusAreas | string[] | Specific vulnerability patterns to look for |
| severityGuidance | string | How to rate severity for this category |
| redGuidance | string | Prompt instructions for Red agent |
| blueGuidance | string | Prompt instructions for Blue agent |

### BattleConfig

Configuration for a battle session.

| Field | Type | Description |
|-------|------|-------------|
| targetDir | string | Absolute path to the target codebase |
| scenario | Scenario | The loaded scenario definition |
| rounds | number | Number of rounds to run (default: 5) |
| provider | Provider | LLM provider instance |

### Battle

The top-level battle session object.

| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique battle ID (nanoid, 8 chars) |
| config | BattleConfig | Battle configuration |
| rounds | Round[] | Completed rounds |
| events | BattleEvent[] | Full event log |
| status | BattleStatus | Current state |
| startedAt | Date | Battle start timestamp |
| endedAt | Date (optional) | Battle end timestamp |

### BattleStatus

```
Enum: "pending" | "running" | "completed" | "interrupted" | "error"
```

### BattleEvent (discriminated union)

All events share a base shape, discriminated by `type`:

| Field | Type | Description |
|-------|------|-------------|
| type | string | Event discriminator (see below) |
| timestamp | Date | When the event occurred |
| data | varies | Event-specific payload |

**Event types**:

| Type | Data | Description |
|------|------|-------------|
| battle-start | { battleId, scenario, targetDir } | Battle session begins |
| round-start | { roundNumber } | New round begins |
| attack | { roundNumber, findings: Finding[] } | Red agent completes turn |
| defend | { roundNumber, mitigations: Mitigation[] } | Blue agent completes turn |
| round-end | { roundNumber, findingCount, mitigationCount } | Round completes |
| battle-end | { battleId, status, summary } | Battle session ends |
| error | { message, phase } | Error occurred |

## Relationships

```
Battle 1──* Round 1──* Finding
                   1──* Mitigation
Battle 1──1 Scenario
Battle 1──1 BattleConfig
Battle 1──* BattleEvent
Finding 1──1 Mitigation (linked by findingId)
```

## State Transitions

```
Battle: pending → running → completed
                         → interrupted (SIGINT)
                         → error (LLM/filesystem failure)
```

Transitions are one-way. A battle cannot restart or resume. Each transition emits a corresponding BattleEvent.
