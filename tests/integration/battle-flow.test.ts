import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { mkdtempSync, writeFileSync, rmSync, mkdirSync } from "node:fs";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { BattleEngine } from "../../src/core/battle-engine.js";
import type { Agent } from "../../src/agents/agent.js";
import type { AgentContext, Scenario, BattleConfig } from "../../src/types.js";

// Mock agent that returns predictable output
class MockRedAgent implements Agent {
  async *analyze(_context: AgentContext): AsyncIterable<string> {
    const output = `I found a vulnerability in the code.

\`\`\`json
[
  {
    "filePath": "app.ts",
    "lineReference": "5",
    "description": "Hardcoded secret found",
    "attackVector": "Token forgery",
    "severity": "high",
    "codeSnippet": "const SECRET = 'abc123'"
  }
]
\`\`\``;
    yield output;
  }
}

class MockBlueAgent implements Agent {
  async *analyze(_context: AgentContext): AsyncIterable<string> {
    const output = `I acknowledge the finding and propose a fix.

\`\`\`json
[
  {
    "acknowledgment": "Valid finding - hardcoded secret detected",
    "proposedFix": "Move to environment variable: process.env.SECRET",
    "confidence": "high"
  }
]
\`\`\``;
    yield output;
  }
}

const mockScenario: Scenario = {
  name: "test-scenario",
  description: "Test scenario",
  focusAreas: ["hardcoded secrets"],
  severityGuidance: "High for any hardcoded secret",
  redGuidance: "Find secrets",
  blueGuidance: "Fix secrets",
};

describe("Battle Flow Integration", () => {
  let tempDir: string;

  beforeEach(() => {
    tempDir = mkdtempSync(join(tmpdir(), "battle-test-"));
    writeFileSync(
      join(tempDir, "app.ts"),
      'const SECRET = "abc123";\nexport function getSecret() { return SECRET; }\n'
    );
  });

  afterEach(() => {
    rmSync(tempDir, { recursive: true, force: true });
  });

  it("should run a complete battle with mock agents", async () => {
    const config: BattleConfig = {
      targetDir: tempDir,
      scenario: mockScenario,
      rounds: 2,
    };

    const engine = new BattleEngine({
      redAgent: new MockRedAgent(),
      blueAgent: new MockBlueAgent(),
      config,
    });

    const battle = await engine.run();

    expect(battle.status).toBe("completed");
    expect(battle.rounds).toHaveLength(2);
    expect(battle.id).toBeTruthy();
    expect(battle.startedAt).toBeInstanceOf(Date);
    expect(battle.endedAt).toBeInstanceOf(Date);
  });

  it("should emit events in correct order", async () => {
    const config: BattleConfig = {
      targetDir: tempDir,
      scenario: mockScenario,
      rounds: 1,
    };

    const engine = new BattleEngine({
      redAgent: new MockRedAgent(),
      blueAgent: new MockBlueAgent(),
      config,
    });

    const battle = await engine.run();
    const eventTypes = battle.events.map((e) => e.type);

    expect(eventTypes[0]).toBe("battle-start");
    expect(eventTypes[1]).toBe("round-start");
    expect(eventTypes[2]).toBe("attack");
    expect(eventTypes[3]).toBe("defend");
    expect(eventTypes[4]).toBe("round-end");
    expect(eventTypes[eventTypes.length - 1]).toBe("battle-end");
  });

  it("should collect findings and mitigations", async () => {
    const config: BattleConfig = {
      targetDir: tempDir,
      scenario: mockScenario,
      rounds: 1,
    };

    const engine = new BattleEngine({
      redAgent: new MockRedAgent(),
      blueAgent: new MockBlueAgent(),
      config,
    });

    const battle = await engine.run();
    const round = battle.rounds[0];

    expect(round.findings.length).toBeGreaterThan(0);
    expect(round.findings[0].severity).toBe("high");
    expect(round.findings[0].filePath).toBe("app.ts");
    expect(round.mitigations.length).toBeGreaterThan(0);
  });

  it("should handle interruption gracefully", async () => {
    // Use a slow agent that yields chunks with delays
    class SlowRedAgent implements Agent {
      async *analyze(_context: AgentContext): AsyncIterable<string> {
        yield "Analyzing...";
        await new Promise((r) => setTimeout(r, 100));
        yield '\n```json\n[{"filePath":"a.ts","lineReference":"1","description":"test","attackVector":"test","severity":"high"}]\n```';
      }
    }

    const config: BattleConfig = {
      targetDir: tempDir,
      scenario: mockScenario,
      rounds: 10,
    };

    const engine = new BattleEngine({
      redAgent: new SlowRedAgent(),
      blueAgent: new MockBlueAgent(),
      config,
    });

    // Interrupt after first round starts
    setTimeout(() => engine.interrupt(), 150);

    const battle = await engine.run();

    expect(battle.status).toBe("interrupted");
    expect(battle.rounds.length).toBeLessThan(10);
  });

  it("should error when target has no source files", async () => {
    const emptyDir = mkdtempSync(join(tmpdir(), "empty-test-"));

    const config: BattleConfig = {
      targetDir: emptyDir,
      scenario: mockScenario,
      rounds: 1,
    };

    const engine = new BattleEngine({
      redAgent: new MockRedAgent(),
      blueAgent: new MockBlueAgent(),
      config,
    });

    await expect(engine.run()).rejects.toThrow("No source files found");

    rmSync(emptyDir, { recursive: true, force: true });
  });
});
