import { describe, it, expect } from "vitest";
import { parseFindings, parseMitigations } from "../../src/agents/response-parser.js";
import type { Finding, Mitigation } from "../../src/types.js";

// --- Helpers ---

function buildJsonBlock(obj: unknown): string {
  return "```json\n" + JSON.stringify(obj, null, 2) + "\n```";
}

// --- parseFindings ---

describe("parseFindings()", () => {
  describe("valid JSON block", () => {
    it("parses a single finding from a JSON block", () => {
      const finding = {
        filePath: "src/db.ts",
        lineReference: "42",
        description: "SQL injection via concatenation",
        attackVector: "User-controlled input in raw SQL",
        severity: "high",
      };
      const raw = "Analysis complete.\n\n" + buildJsonBlock([finding]);

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value).toHaveLength(1);
      expect(result.value[0].description).toBe("SQL injection via concatenation");
      expect(result.value[0].severity).toBe("high");
      expect(result.value[0].filePath).toBe("src/db.ts");
      expect(result.value[0].lineReference).toBe("42");
      expect(result.value[0].attackVector).toBe("User-controlled input in raw SQL");
    });

    it("assigns the correct roundNumber to parsed findings", () => {
      const finding = {
        filePath: "src/auth.ts",
        lineReference: "10",
        description: "Auth bypass",
        attackVector: "Missing check",
        severity: "critical",
      };
      const raw = buildJsonBlock([finding]);

      const result = parseFindings(raw, 3);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].roundNumber).toBe(3);
    });

    it("assigns a non-empty id to each finding", () => {
      const finding = {
        filePath: "src/api.ts",
        lineReference: "5",
        description: "Unvalidated redirect",
        attackVector: "Open redirect",
        severity: "medium",
      };
      const raw = buildJsonBlock([finding]);

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(typeof result.value[0].id).toBe("string");
      expect(result.value[0].id.length).toBeGreaterThan(0);
    });

    it("handles unknown severity by defaulting to 'medium'", () => {
      const finding = {
        filePath: "src/x.ts",
        lineReference: "1",
        description: "Some issue",
        attackVector: "Some vector",
        severity: "super-critical-ultra",
      };
      const raw = buildJsonBlock([finding]);

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].severity).toBe("medium");
    });

    it("parses codeSnippet when provided", () => {
      const finding = {
        filePath: "src/db.ts",
        lineReference: "99",
        description: "Snippet test",
        attackVector: "Direct injection",
        severity: "high",
        codeSnippet: 'query("SELECT * FROM users WHERE id=" + id)',
      };
      const raw = buildJsonBlock([finding]);

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].codeSnippet).toBe('query("SELECT * FROM users WHERE id=" + id)');
    });

    it("returns ok:true with an empty array when JSON block contains an empty array", () => {
      const raw = buildJsonBlock([]);

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value).toHaveLength(0);
    });
  });

  describe("no JSON blocks (fallback behavior)", () => {
    it("returns ok:true with a single fallback finding when there are no JSON blocks", () => {
      const raw = "The code has an issue with authentication at line 50.";

      const result = parseFindings(raw, 2);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value).toHaveLength(1);
    });

    it("fallback finding contains a slice of the raw output as description", () => {
      const raw = "No structured data here — just free text analysis.";

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].description).toContain("No structured data here");
    });

    it("fallback finding has roundNumber set correctly", () => {
      const raw = "Plain text only.";

      const result = parseFindings(raw, 5);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].roundNumber).toBe(5);
    });

    it("fallback finding defaults severity to 'medium'", () => {
      const raw = "Something suspicious was found.";

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].severity).toBe("medium");
    });

    it("fallback finding has filePath of 'unknown'", () => {
      const raw = "An issue was detected.";

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].filePath).toBe("unknown");
    });
  });

  describe("multiple JSON blocks", () => {
    it("parses findings from multiple JSON blocks and merges them", () => {
      const block1 = buildJsonBlock([
        { filePath: "a.ts", lineReference: "1", description: "Issue A", attackVector: "Vector A", severity: "high" },
      ]);
      const block2 = buildJsonBlock([
        { filePath: "b.ts", lineReference: "2", description: "Issue B", attackVector: "Vector B", severity: "low" },
        { filePath: "c.ts", lineReference: "3", description: "Issue C", attackVector: "Vector C", severity: "critical" },
      ]);
      const raw = "First block:\n" + block1 + "\n\nSecond block:\n" + block2;

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value).toHaveLength(3);

      const descriptions = result.value.map((f) => f.description);
      expect(descriptions).toContain("Issue A");
      expect(descriptions).toContain("Issue B");
      expect(descriptions).toContain("Issue C");
    });

    it("skips malformed JSON blocks and continues parsing valid ones", () => {
      const badBlock = "```json\n{ this is not valid json }\n```";
      const goodBlock = buildJsonBlock([
        { filePath: "ok.ts", lineReference: "10", description: "Valid finding", attackVector: "Real vector", severity: "medium" },
      ]);
      const raw = badBlock + "\n\n" + goodBlock;

      const result = parseFindings(raw, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value.length).toBeGreaterThanOrEqual(1);
      const validFinding = result.value.find((f) => f.description === "Valid finding");
      expect(validFinding).toBeDefined();
    });

    it("each finding from multiple blocks gets a unique id", () => {
      const block = buildJsonBlock([
        { filePath: "a.ts", lineReference: "1", description: "A", attackVector: "V", severity: "low" },
        { filePath: "b.ts", lineReference: "2", description: "B", attackVector: "V", severity: "low" },
      ]);

      const result = parseFindings(block, 1);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      const ids = result.value.map((f) => f.id);
      const uniqueIds = new Set(ids);
      expect(uniqueIds.size).toBe(ids.length);
    });
  });
});

// --- parseMitigations ---

describe("parseMitigations()", () => {
  describe("valid JSON block", () => {
    it("parses a single mitigation from a JSON block", () => {
      const mit = {
        findingId: "find-001",
        acknowledgment: "Confirmed SQL injection",
        proposedFix: "Use parameterized queries",
        confidence: "high",
      };
      const raw = "Defense analysis:\n\n" + buildJsonBlock([mit]);
      const findingIds = ["find-001"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value.length).toBeGreaterThanOrEqual(1);
      const m = result.value.find((x) => x.findingId === "find-001");
      expect(m).toBeDefined();
      expect(m!.proposedFix).toBe("Use parameterized queries");
      expect(m!.confidence).toBe("high");
    });

    it("sets roundNumber on each mitigation", () => {
      const mit = {
        findingId: "find-001",
        acknowledgment: "Ack",
        proposedFix: "Fix",
        confidence: "medium",
      };
      const raw = buildJsonBlock([mit]);

      const result = parseMitigations(raw, 4, ["find-001"]);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].roundNumber).toBe(4);
    });

    it("assigns a non-empty id to each mitigation", () => {
      const mit = {
        findingId: "find-abc",
        acknowledgment: "Ack",
        proposedFix: "Fix it",
        confidence: "low",
      };
      const raw = buildJsonBlock([mit]);

      const result = parseMitigations(raw, 1, ["find-abc"]);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(typeof result.value[0].id).toBe("string");
      expect(result.value[0].id.length).toBeGreaterThan(0);
    });

    it("defaults confidence to 'medium' for unknown confidence values", () => {
      const mit = {
        findingId: "find-001",
        acknowledgment: "Ack",
        proposedFix: "Fix",
        confidence: "extreme",
      };
      const raw = buildJsonBlock([mit]);

      const result = parseMitigations(raw, 1, ["find-001"]);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].confidence).toBe("medium");
    });
  });

  describe("mitigations matching finding IDs", () => {
    it("creates one mitigation per finding ID when there are no JSON blocks", () => {
      const raw = "I have reviewed the findings and here are my recommendations.";
      const findingIds = ["f1", "f2", "f3"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value).toHaveLength(3);
    });

    it("fallback mitigations reference their corresponding finding IDs", () => {
      const raw = "General mitigation advice for all findings.";
      const findingIds = ["find-A", "find-B"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      const ids = result.value.map((m) => m.findingId);
      expect(ids).toContain("find-A");
      expect(ids).toContain("find-B");
    });

    it("fills gaps when fewer mitigations are parsed than findings", () => {
      // 1 mitigation in JSON but 3 finding IDs — should pad to 3
      const mit = {
        findingId: "f1",
        acknowledgment: "Ack",
        proposedFix: "Fix for f1",
        confidence: "high",
      };
      const raw = buildJsonBlock([mit]);
      const findingIds = ["f1", "f2", "f3"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value).toHaveLength(3);

      const findingIdSet = new Set(result.value.map((m) => m.findingId));
      // f1 comes from the JSON block; f2 and f3 are gap-filled
      expect(findingIdSet.has("f1")).toBe(true);
    });

    it("returns ok:true with empty mitigations when findingIds is empty and no JSON", () => {
      const raw = "Nothing to mitigate.";

      const result = parseMitigations(raw, 1, []);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value).toHaveLength(0);
    });

    it("uses findingId from JSON when explicitly provided", () => {
      const mit = {
        findingId: "explicit-id-999",
        acknowledgment: "Confirmed",
        proposedFix: "Fix explicitly",
        confidence: "high",
      };
      const raw = buildJsonBlock([mit]);
      const findingIds = ["explicit-id-999", "other-id"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].findingId).toBe("explicit-id-999");
    });
  });

  describe("fallback (no JSON blocks)", () => {
    it("fallback mitigations contain a slice of the raw text as proposedFix", () => {
      const raw = "Apply input validation and use prepared statements throughout the codebase.";
      const findingIds = ["f1"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].proposedFix).toContain("Apply input validation");
    });

    it("fallback mitigations have acknowledgment set to 'Acknowledged'", () => {
      const raw = "General advice here.";
      const findingIds = ["f1"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].acknowledgment).toBe("Acknowledged");
    });

    it("fallback mitigations default confidence to 'medium'", () => {
      const raw = "Some advice.";
      const findingIds = ["f1"];

      const result = parseMitigations(raw, 1, findingIds);

      expect(result.ok).toBe(true);
      if (!result.ok) return;
      expect(result.value[0].confidence).toBe("medium");
    });
  });
});
