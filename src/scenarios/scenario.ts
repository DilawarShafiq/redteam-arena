/**
 * Scenario type definition and Markdown frontmatter loader.
 * Parses scenario files: YAML frontmatter + Red/Blue guidance sections.
 */

import { readFile, readdir } from "node:fs/promises";
import { join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { dirname } from "node:path";
import yaml from "js-yaml";
import type { Scenario, Result } from "../types.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const BUILTIN_DIR = resolve(__dirname, "..", "scenarios", "builtin");

interface ScenarioFrontmatter {
  name: string;
  description: string;
  focus_areas: string[];
  severity_guidance: string;
  is_meta?: boolean;
  sub_scenarios?: string[];
}

function parseFrontmatter(
  raw: string
): Result<{ frontmatter: ScenarioFrontmatter; body: string }> {
  const parts = raw.split("---");
  if (parts.length < 3) {
    return {
      ok: false,
      error: new Error("Invalid scenario file: missing --- frontmatter delimiters"),
    };
  }

  const yamlContent = parts[1].trim();
  const body = parts.slice(2).join("---").trim();

  try {
    const frontmatter = yaml.load(yamlContent) as ScenarioFrontmatter;
    if (!frontmatter.name || !frontmatter.description) {
      return {
        ok: false,
        error: new Error(
          "Invalid scenario frontmatter: missing name or description"
        ),
      };
    }
    return { ok: true, value: { frontmatter, body } };
  } catch (err) {
    return {
      ok: false,
      error: new Error(`Failed to parse scenario YAML: ${err}`),
    };
  }
}

function parseGuidanceSections(body: string): {
  redGuidance: string;
  blueGuidance: string;
} {
  let redGuidance = "";
  let blueGuidance = "";

  const redMatch = body.match(
    /## Red Agent Guidance\s*\n([\s\S]*?)(?=## Blue Agent Guidance|$)/
  );
  const blueMatch = body.match(/## Blue Agent Guidance\s*\n([\s\S]*?)$/);

  if (redMatch) redGuidance = redMatch[1].trim();
  if (blueMatch) blueGuidance = blueMatch[1].trim();

  return { redGuidance, blueGuidance };
}

export async function loadScenario(name: string): Promise<Result<Scenario>> {
  // Try builtin directory first, then compiled dist path
  const paths = [
    join(BUILTIN_DIR, `${name}.md`),
    resolve(__dirname, "builtin", `${name}.md`),
  ];

  let raw: string | undefined;
  for (const filePath of paths) {
    try {
      raw = await readFile(filePath, "utf-8");
      break;
    } catch {
      continue;
    }
  }

  if (!raw) {
    return {
      ok: false,
      error: new Error(`Scenario not found: ${name}`),
    };
  }

  const parsed = parseFrontmatter(raw);
  if (!parsed.ok) return parsed;

  const { frontmatter, body } = parsed.value;
  const { redGuidance, blueGuidance } = parseGuidanceSections(body);

  return {
    ok: true,
    value: {
      name: frontmatter.name,
      description: frontmatter.description,
      focusAreas: frontmatter.focus_areas || [],
      severityGuidance: frontmatter.severity_guidance || "",
      redGuidance,
      blueGuidance,
      isMeta: frontmatter.is_meta || false,
      subScenarios: frontmatter.sub_scenarios || [],
    },
  };
}

export async function listScenarios(): Promise<Scenario[]> {
  const scenarios: Scenario[] = [];
  const dirs = [BUILTIN_DIR, resolve(__dirname, "builtin")];

  for (const dir of dirs) {
    try {
      const files = await readdir(dir);
      for (const file of files) {
        if (!file.endsWith(".md")) continue;
        const name = file.replace(".md", "");
        const result = await loadScenario(name);
        if (result.ok) {
          // Avoid duplicates
          if (!scenarios.some((s) => s.name === result.value.name)) {
            scenarios.push(result.value);
          }
        }
      }
      if (scenarios.length > 0) break; // Found scenarios in first valid dir
    } catch {
      continue;
    }
  }

  return scenarios;
}
