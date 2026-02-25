<div align="center">

# RedTeam Arena

**AI vs AI adversarial security testing for your codebase.**

[![npm version](https://img.shields.io/npm/v/redteam-arena.svg)](https://www.npmjs.com/package/redteam-arena)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/DilawarShafiq/redteam-arena/actions/workflows/ci.yml/badge.svg)](https://github.com/DilawarShafiq/redteam-arena/actions/workflows/ci.yml)
[![Node.js](https://img.shields.io/badge/node-%3E%3D18-brightgreen.svg)](https://nodejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-strict-blue.svg)](https://www.typescriptlang.org/)

Red team agents attack. Blue team agents defend. Fully automated.

</div>

---

## Why?

- **Proactive, not reactive** — AI agents that think like attackers probe your code 24/7, instead of waiting for the next CVE.
- **Attack + defense in one run** — every vulnerability found gets an immediate mitigation proposal, so you ship fixes, not just findings.
- **Zero setup** — point it at a directory, pick a scenario, get a report. No config files, no infrastructure, no learning curve.

## Quick Start

```bash
# Install globally
npm install -g redteam-arena

# Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# Run a battle
redteam-arena battle ./my-project --scenario sql-injection
```

### What you'll see

```
  REDTEAM ARENA v0.1.0
  Scenario: sql-injection | Target: ./my-project
  ==================================================

  Round 1/5
  ----------------------------------------

  RED AGENT (Attacker):
  ...streaming analysis...

  BLUE AGENT (Defender):
  ...streaming mitigations...

  Round 1: 3 finding(s), 3 mitigation(s)

  ==================================================
  Battle Report Summary
  ==================================================

  Rounds: 5  |  Vulnerabilities: 8
   Critical: 2   |  High: 3  |  Medium: 2  |  Low: 1
  Mitigations proposed: 7/8 (88%)

  Full report: ./reports/battle-abc123.md
```

## CLI Reference

### `redteam-arena battle <directory>`

Run a security battle against a target codebase.

| Option | Description | Default |
|--------|-------------|---------|
| `-s, --scenario <name>` | Scenario to run (required) | — |
| `-r, --rounds <number>` | Number of battle rounds | `5` |

```bash
# 3 rounds of XSS testing
redteam-arena battle ./webapp --scenario xss --rounds 3

# Full audit (runs all scenarios sequentially)
redteam-arena battle ./api --scenario full-audit
```

### `redteam-arena list`

List all available scenarios.

```bash
redteam-arena list
```

## Built-in Scenarios

| Scenario | Description |
|----------|-------------|
| `sql-injection` | Find SQL injection vectors in database queries |
| `xss` | Detect cross-site scripting vulnerabilities |
| `auth-bypass` | Find authentication and authorization flaws |
| `secrets-exposure` | Detect hardcoded secrets and leaked credentials |
| `full-audit` | Run all scenarios sequentially |

## How It Works

1. **Read** — RedTeam Arena reads the source files in your target directory.
2. **Attack** — The Red Agent (Claude) analyzes the code for vulnerabilities based on the chosen scenario, producing structured findings with severity, file location, and attack vectors.
3. **Defend** — The Blue Agent (Claude) reviews each finding and proposes concrete mitigations with code fixes and confidence levels.
4. **Report** — A Markdown battle report is generated with all findings, mitigations, and a severity summary.

Each battle runs multiple rounds. In each round, the Red Agent digs deeper based on previous findings, and the Blue Agent refines its defenses.

## Programmatic API

RedTeam Arena exports its core components for use in your own tools:

```typescript
import {
  BattleEngine,
  RedAgent,
  BlueAgent,
  ClaudeAdapter,
  loadScenario,
  generateReport,
} from "redteam-arena";

const provider = new ClaudeAdapter();
const redAgent = new RedAgent(provider);
const blueAgent = new BlueAgent(provider);

const scenario = await loadScenario("sql-injection");
if (!scenario.ok) throw new Error("Scenario not found");

const engine = new BattleEngine({
  redAgent,
  blueAgent,
  config: {
    targetDir: "./my-project",
    scenario: scenario.value,
    rounds: 3,
  },
});

const battle = await engine.run();
const report = generateReport(battle);
console.log(report);
```

## Requirements

- **Node.js** >= 18
- **Anthropic API key** — set `ANTHROPIC_API_KEY` in your environment ([get one here](https://console.anthropic.com/))

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, project structure, and how to add new scenarios.

## Security

To report a security vulnerability, see [SECURITY.md](SECURITY.md).

## License

[MIT](LICENSE) — Muhammad Dilawar Shafiq (Dilawar Gopang)
