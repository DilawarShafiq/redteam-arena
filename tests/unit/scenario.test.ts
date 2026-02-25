import { describe, it, expect } from "vitest";
import { loadScenario, listScenarios } from "../../src/scenarios/scenario.js";

describe("loadScenario()", () => {
  it("loads a valid scenario by name without error", async () => {
    const result = await loadScenario("sql-injection");

    expect(result.ok).toBe(true);
  });

  it("loaded scenario has the expected top-level fields", async () => {
    const result = await loadScenario("sql-injection");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const scenario = result.value;
    expect(scenario).toHaveProperty("name");
    expect(scenario).toHaveProperty("description");
    expect(scenario).toHaveProperty("focusAreas");
    expect(scenario).toHaveProperty("redGuidance");
    expect(scenario).toHaveProperty("blueGuidance");
  });

  it("loaded scenario name and description are non-empty strings", async () => {
    const result = await loadScenario("sql-injection");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(typeof result.value.name).toBe("string");
    expect(result.value.name.length).toBeGreaterThan(0);
    expect(typeof result.value.description).toBe("string");
    expect(result.value.description.length).toBeGreaterThan(0);
  });

  it("loaded scenario has focusAreas as a non-empty array", async () => {
    const result = await loadScenario("sql-injection");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(Array.isArray(result.value.focusAreas)).toBe(true);
    expect(result.value.focusAreas.length).toBeGreaterThan(0);
  });

  it("loaded scenario has redGuidance containing relevant content", async () => {
    const result = await loadScenario("sql-injection");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.value.redGuidance.length).toBeGreaterThan(0);
  });

  it("loaded scenario has blueGuidance containing relevant content", async () => {
    const result = await loadScenario("sql-injection");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.value.blueGuidance.length).toBeGreaterThan(0);
  });

  it("returns an error Result for a non-existent scenario", async () => {
    const result = await loadScenario("this-scenario-does-not-exist");

    expect(result.ok).toBe(false);
    if (result.ok) return;

    expect(result.error).toBeInstanceOf(Error);
    expect(result.error.message).toMatch(/not found/i);
  });

  it("returns an error Result for an empty string scenario name", async () => {
    const result = await loadScenario("");

    expect(result.ok).toBe(false);
  });
});

describe("listScenarios()", () => {
  it("returns an array", async () => {
    const scenarios = await listScenarios();

    expect(Array.isArray(scenarios)).toBe(true);
  });

  it("returns at least one scenario", async () => {
    const scenarios = await listScenarios();

    expect(scenarios.length).toBeGreaterThan(0);
  });

  it("each scenario in the list has required fields", async () => {
    const scenarios = await listScenarios();

    for (const scenario of scenarios) {
      expect(scenario).toHaveProperty("name");
      expect(scenario).toHaveProperty("description");
      expect(scenario).toHaveProperty("focusAreas");
      expect(scenario).toHaveProperty("redGuidance");
      expect(scenario).toHaveProperty("blueGuidance");
    }
  });

  it("includes the sql-injection scenario", async () => {
    const scenarios = await listScenarios();

    const found = scenarios.some((s) => s.name === "sql-injection");
    expect(found).toBe(true);
  });

  it("full-audit is a meta scenario with subScenarios", async () => {
    const result = await loadScenario("full-audit");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const scenario = result.value;
    expect(scenario.isMeta).toBe(true);
    expect(Array.isArray(scenario.subScenarios)).toBe(true);
    expect(scenario.subScenarios!.length).toBeGreaterThan(0);
  });

  it("full-audit subScenarios reference known scenario names", async () => {
    const result = await loadScenario("full-audit");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    const subScenarios = result.value.subScenarios!;
    expect(subScenarios).toContain("sql-injection");
  });

  it("non-meta scenarios have isMeta false or undefined", async () => {
    const result = await loadScenario("sql-injection");

    expect(result.ok).toBe(true);
    if (!result.ok) return;

    expect(result.value.isMeta).toBeFalsy();
  });
});
