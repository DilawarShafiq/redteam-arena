/**
 * Response parser — extracts structured JSON blocks from agent output.
 * Agents stream natural language with embedded ```json blocks.
 */

import { nanoid } from "nanoid";
import type { Finding, Mitigation, Result, Severity } from "../types.js";

const SEVERITY_VALUES = new Set(["critical", "high", "medium", "low"]);
const CONFIDENCE_VALUES = new Set(["high", "medium", "low"]);

function extractJsonBlocks(text: string): string[] {
  const blocks: string[] = [];
  const regex = /```json\s*\n([\s\S]*?)```/g;
  let match: RegExpExecArray | null;

  while ((match = regex.exec(text)) !== null) {
    blocks.push(match[1].trim());
  }

  return blocks;
}

function isValidSeverity(s: unknown): s is Severity {
  return typeof s === "string" && SEVERITY_VALUES.has(s.toLowerCase());
}

function isValidConfidence(c: unknown): c is "high" | "medium" | "low" {
  return typeof c === "string" && CONFIDENCE_VALUES.has(c.toLowerCase());
}

export function parseFindings(
  rawOutput: string,
  roundNumber: number
): Result<Finding[]> {
  const jsonBlocks = extractJsonBlocks(rawOutput);

  if (jsonBlocks.length === 0) {
    // Try to parse the entire output as JSON
    try {
      const parsed = JSON.parse(rawOutput);
      if (Array.isArray(parsed)) {
        return parseFindingsFromArray(parsed, roundNumber);
      }
    } catch {
      // No structured data found — create a single finding from the text
      return {
        ok: true,
        value: [
          {
            id: nanoid(8),
            roundNumber,
            filePath: "unknown",
            lineReference: "0",
            description: rawOutput.slice(0, 500),
            attackVector: "See description",
            severity: "medium" as Severity,
          },
        ],
      };
    }
  }

  const allFindings: Finding[] = [];

  for (const block of jsonBlocks) {
    try {
      const parsed = JSON.parse(block);
      const items = Array.isArray(parsed) ? parsed : [parsed];
      const result = parseFindingsFromArray(items, roundNumber);
      if (result.ok) {
        allFindings.push(...result.value);
      }
    } catch {
      continue;
    }
  }

  return { ok: true, value: allFindings };
}

function parseFindingsFromArray(
  items: unknown[],
  roundNumber: number
): Result<Finding[]> {
  const findings: Finding[] = [];

  for (const item of items) {
    if (typeof item !== "object" || item === null) continue;

    const obj = item as Record<string, unknown>;
    const severity = isValidSeverity(obj.severity)
      ? (obj.severity as Severity)
      : "medium";

    findings.push({
      id: nanoid(8),
      roundNumber,
      filePath: String(obj.filePath || obj.file_path || obj.file || "unknown"),
      lineReference: String(
        obj.lineReference || obj.line_reference || obj.line || "0"
      ),
      description: String(obj.description || obj.desc || "No description"),
      attackVector: String(
        obj.attackVector || obj.attack_vector || obj.attack || "Not specified"
      ),
      severity,
      codeSnippet: obj.codeSnippet
        ? String(obj.codeSnippet)
        : obj.code_snippet
          ? String(obj.code_snippet)
          : undefined,
    });
  }

  return { ok: true, value: findings };
}

export function parseMitigations(
  rawOutput: string,
  roundNumber: number,
  findingIds: string[]
): Result<Mitigation[]> {
  const jsonBlocks = extractJsonBlocks(rawOutput);

  if (jsonBlocks.length === 0) {
    // Create mitigations from raw text, one per finding
    return {
      ok: true,
      value: findingIds.map((findingId) => ({
        id: nanoid(8),
        findingId,
        roundNumber,
        acknowledgment: "Acknowledged",
        proposedFix: rawOutput.slice(0, 500),
        confidence: "medium" as const,
      })),
    };
  }

  const allMitigations: Mitigation[] = [];

  for (const block of jsonBlocks) {
    try {
      const parsed = JSON.parse(block);
      const items = Array.isArray(parsed) ? parsed : [parsed];

      for (let i = 0; i < items.length; i++) {
        const obj = items[i] as Record<string, unknown>;
        const matchingFindingId =
          String(obj.findingId || obj.finding_id || "") ||
          findingIds[i] ||
          findingIds[0] ||
          "unknown";
        const confidence = isValidConfidence(obj.confidence)
          ? (obj.confidence as "high" | "medium" | "low")
          : "medium";

        allMitigations.push({
          id: nanoid(8),
          findingId: matchingFindingId,
          roundNumber,
          acknowledgment: String(
            obj.acknowledgment || obj.assessment || "Acknowledged"
          ),
          proposedFix: String(
            obj.proposedFix ||
              obj.proposed_fix ||
              obj.fix ||
              obj.mitigation ||
              "See response"
          ),
          confidence,
        });
      }
    } catch {
      continue;
    }
  }

  // If we parsed some but not enough for all findings, fill gaps
  if (allMitigations.length < findingIds.length) {
    for (let i = allMitigations.length; i < findingIds.length; i++) {
      allMitigations.push({
        id: nanoid(8),
        findingId: findingIds[i],
        roundNumber,
        acknowledgment: "Acknowledged",
        proposedFix: "See battle log for details",
        confidence: "medium",
      });
    }
  }

  return { ok: true, value: allMitigations };
}
