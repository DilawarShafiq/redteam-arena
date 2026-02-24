import { describe, it, expect } from "vitest";
import { generateReport } from "../../src/reports/battle-report.js";
import type { Battle, Finding, Mitigation, Round } from "../../src/types.js";

// --- Helpers ---

function makeFinding(overrides: Partial<Finding> = {}): Finding {
  return {
    id: "find-001",
    roundNumber: 1,
    filePath: "src/db/queries.ts",
    lineReference: "42",
    description: "SQL injection via string concatenation in user query",
    attackVector: "Unsanitized user input passed directly into SQL string",
    severity: "high",
    ...overrides,
  };
}

function makeMitigation(overrides: Partial<Mitigation> = {}): Mitigation {
  return {
    id: "mit-001",
    findingId: "find-001",
    roundNumber: 1,
    acknowledgment: "Confirmed SQL injection vulnerability",
    proposedFix: "Replace string concatenation with parameterized queries",
    confidence: "high",
    ...overrides,
  };
}

function makeRound(
  number: number,
  findings: Finding[],
  mitigations: Mitigation[]
): Round {
  return {
    number,
    findings,
    mitigations,
    redRawOutput: `Round ${number} red agent output`,
    blueRawOutput: `Round ${number} blue agent output`,
  };
}

function makeBattle(rounds: Round[]): Battle {
  return {
    id: "battle-abc-123",
    config: {
      targetDir: "/home/user/project",
      scenario: {
        name: "sql-injection",
        description: "Find SQL injection vectors",
        focusAreas: ["Raw SQL", "User input"],
        severityGuidance: "Critical for direct injection",
        redGuidance: "Look for string concatenation",
        blueGuidance: "Use parameterized queries",
        isMeta: false,
        subScenarios: [],
      },
      rounds: rounds.length,
    },
    rounds,
    events: [],
    status: "completed",
    startedAt: new Date("2024-01-15T10:00:00Z"),
    endedAt: new Date("2024-01-15T10:05:00Z"),
  };
}

// --- Tests ---

describe("generateReport()", () => {
  describe("battle ID", () => {
    it("includes the battle ID in the report", () => {
      const battle = makeBattle([makeRound(1, [], [])]);
      const report = generateReport(battle);

      expect(report).toContain("battle-abc-123");
    });

    it("places battle ID in the header table", () => {
      const battle = makeBattle([makeRound(1, [], [])]);
      const report = generateReport(battle);

      // The report uses a markdown table: | **Battle ID** | <id> |
      expect(report).toMatch(/\*\*Battle ID\*\*.*battle-abc-123/);
    });
  });

  describe("severity counts", () => {
    it("shows severity counts in the summary table", () => {
      const findings: Finding[] = [
        makeFinding({ id: "f1", severity: "critical" }),
        makeFinding({ id: "f2", severity: "high" }),
        makeFinding({ id: "f3", severity: "high" }),
        makeFinding({ id: "f4", severity: "medium" }),
        makeFinding({ id: "f5", severity: "low" }),
      ];
      const round = makeRound(1, findings, []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      // The summary table should have the correct counts
      expect(report).toContain("| Critical | 1 |");
      expect(report).toContain("| High | 2 |");
      expect(report).toContain("| Medium | 1 |");
      expect(report).toContain("| Low | 1 |");
    });

    it("shows zero counts for severities not present", () => {
      const findings: Finding[] = [
        makeFinding({ id: "f1", severity: "critical" }),
      ];
      const round = makeRound(1, findings, []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("| Critical | 1 |");
      expect(report).toContain("| High | 0 |");
      expect(report).toContain("| Medium | 0 |");
      expect(report).toContain("| Low | 0 |");
    });

    it("shows total finding count across multiple rounds", () => {
      const round1 = makeRound(1, [makeFinding({ id: "f1" })], []);
      const round2 = makeRound(2, [makeFinding({ id: "f2" }), makeFinding({ id: "f3" })], []);
      const battle = makeBattle([round1, round2]);

      const report = generateReport(battle);

      expect(report).toContain("**Total** | **3**");
    });
  });

  describe("finding descriptions", () => {
    it("includes the finding description in the report", () => {
      const finding = makeFinding({ description: "Critical SQL injection in login endpoint" });
      const round = makeRound(1, [finding], []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("Critical SQL injection in login endpoint");
    });

    it("includes the finding file path and line reference", () => {
      const finding = makeFinding({ filePath: "src/auth/login.ts", lineReference: "87" });
      const round = makeRound(1, [finding], []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("src/auth/login.ts:87");
    });

    it("includes the attack vector in the report", () => {
      const finding = makeFinding({ attackVector: "User-controlled username passed to raw query" });
      const round = makeRound(1, [finding], []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("User-controlled username passed to raw query");
    });

    it("includes optional code snippet when present", () => {
      const finding = makeFinding({
        codeSnippet: 'db.query("SELECT * FROM users WHERE id=" + userId)',
      });
      const round = makeRound(1, [finding], []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain('db.query("SELECT * FROM users WHERE id=" + userId)');
    });
  });

  describe("mitigation details", () => {
    it("includes the proposed fix in the report", () => {
      const finding = makeFinding({ id: "find-001" });
      const mitigation = makeMitigation({
        findingId: "find-001",
        proposedFix: "Use db.query('SELECT * FROM users WHERE id = ?', [userId])",
      });
      const round = makeRound(1, [finding], [mitigation]);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("Use db.query('SELECT * FROM users WHERE id = ?', [userId])");
    });

    it("includes the mitigation acknowledgment in the report", () => {
      const finding = makeFinding({ id: "find-001" });
      const mitigation = makeMitigation({
        findingId: "find-001",
        acknowledgment: "This is a confirmed high-severity SQL injection flaw",
      });
      const round = makeRound(1, [finding], [mitigation]);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("This is a confirmed high-severity SQL injection flaw");
    });

    it("includes mitigation confidence in the report", () => {
      const finding = makeFinding({ id: "find-001" });
      const mitigation = makeMitigation({ findingId: "find-001", confidence: "high" });
      const round = makeRound(1, [finding], [mitigation]);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toMatch(/Confidence.*HIGH/i);
    });

    it("shows mitigation coverage percentage in the summary", () => {
      const f1 = makeFinding({ id: "f1" });
      const f2 = makeFinding({ id: "f2" });
      const m1 = makeMitigation({ findingId: "f1" });
      const round = makeRound(1, [f1, f2], [m1]);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      // 1 mitigation / 2 findings = 50%
      expect(report).toContain("1/2");
      expect(report).toContain("50%");
    });
  });

  describe("zero findings", () => {
    it("shows 'No vulnerabilities found' when there are no findings", () => {
      const round = makeRound(1, [], []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("No vulnerabilities found.");
    });

    it("does NOT include the findings detail section body when there are zero findings", () => {
      const round = makeRound(1, [], []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      // Should not contain any finding headers like "Finding 1:"
      expect(report).not.toMatch(/Finding \d+:/);
    });

    it("shows 100% mitigation coverage when there are zero findings", () => {
      const round = makeRound(1, [], []);
      const battle = makeBattle([round]);

      const report = generateReport(battle);

      expect(report).toContain("0/0");
      expect(report).toContain("100%");
    });
  });

  describe("general report structure", () => {
    it("includes the RedTeam Arena header", () => {
      const battle = makeBattle([makeRound(1, [], [])]);
      const report = generateReport(battle);

      expect(report).toContain("# RedTeam Arena Battle Report");
    });

    it("includes the scenario name", () => {
      const battle = makeBattle([makeRound(1, [], [])]);
      const report = generateReport(battle);

      expect(report).toContain("sql-injection");
    });

    it("includes a Battle Log section", () => {
      const battle = makeBattle([makeRound(1, [], [])]);
      const report = generateReport(battle);

      expect(report).toContain("## Battle Log");
    });

    it("returns a non-empty string", () => {
      const battle = makeBattle([makeRound(1, [], [])]);
      const report = generateReport(battle);

      expect(typeof report).toBe("string");
      expect(report.length).toBeGreaterThan(0);
    });
  });
});
