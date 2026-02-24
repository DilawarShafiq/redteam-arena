#!/usr/bin/env node

/**
 * RedTeam Arena CLI — AI vs AI security battles.
 * Entry point for the `redteam-arena` command.
 */

import { Command } from "commander";
import { resolve } from "node:path";
import { access } from "node:fs/promises";
import { loadScenario, listScenarios } from "./scenarios/scenario.js";
import { ClaudeAdapter, validateApiKey } from "./agents/claude-adapter.js";
import { RedAgent } from "./agents/red-agent.js";
import { BlueAgent } from "./agents/blue-agent.js";
import { BattleEngine } from "./core/battle-engine.js";
import { generateReport, writeReport } from "./reports/battle-report.js";
import {
  displayBattleHeader,
  displayBattleSummary,
  displayReportPath,
  displayError,
  displayNoFindings,
  displayInterrupted,
} from "./display.js";
import type { Scenario, BattleConfig } from "./types.js";

const program = new Command();

program
  .name("redteam-arena")
  .description(
    "AI vs AI adversarial security testing. Red team attacks, blue team defends."
  )
  .version("0.1.0");

// --- battle command ---

program
  .command("battle")
  .description("Start a security battle against a target codebase")
  .argument("<directory>", "Path to the target codebase")
  .requiredOption(
    "-s, --scenario <name>",
    "Scenario name (e.g., sql-injection, xss, full-audit)"
  )
  .option("-r, --rounds <number>", "Number of battle rounds", "5")
  .action(async (directory: string, options: { scenario: string; rounds: string }) => {
    try {
      // Pre-flight: API key
      if (!validateApiKey()) {
        displayError(
          "ANTHROPIC_API_KEY environment variable is required.\n  Get your key at https://console.anthropic.com/"
        );
        process.exit(2);
      }

      // Pre-flight: directory exists
      const targetDir = resolve(directory);
      try {
        await access(targetDir);
      } catch {
        displayError(`Directory not found: ${targetDir}`);
        process.exit(2);
      }

      // Pre-flight: scenario
      const scenarioResult = await loadScenario(options.scenario);
      if (!scenarioResult.ok) {
        const available = await listScenarios();
        const names = available.map((s) => s.name).join(", ");
        displayError(
          `Unknown scenario '${options.scenario}'. Available scenarios: ${names}`
        );
        process.exit(2);
      }

      const scenario = scenarioResult.value;
      const rounds = parseInt(options.rounds, 10) || 5;

      // Handle meta-scenarios (full-audit)
      if (scenario.isMeta && scenario.subScenarios && scenario.subScenarios.length > 0) {
        await runMetaBattle(targetDir, scenario, rounds);
      } else {
        await runBattle(targetDir, scenario, rounds);
      }
    } catch (err) {
      displayError(
        err instanceof Error ? err.message : String(err)
      );
      process.exit(1);
    }
  });

// --- list command ---

program
  .command("list")
  .description("List all available scenarios")
  .action(async () => {
    const scenarios = await listScenarios();

    console.log("\nAvailable Scenarios:\n");
    for (const s of scenarios) {
      const name = s.name.padEnd(20);
      console.log(`  ${name}${s.description}`);
    }
    console.log(
      "\nUsage: redteam-arena battle <directory> --scenario <name>\n"
    );
  });

// --- Battle execution ---

async function runBattle(
  targetDir: string,
  scenario: Scenario,
  rounds: number
): Promise<void> {
  const provider = new ClaudeAdapter();
  const redAgent = new RedAgent(provider);
  const blueAgent = new BlueAgent(provider);

  const config: BattleConfig = {
    targetDir,
    scenario,
    rounds,
  };

  const engine = new BattleEngine({
    redAgent,
    blueAgent,
    config,
  });

  // SIGINT handling
  const sigintHandler = () => {
    engine.interrupt();
    displayInterrupted();
  };
  process.on("SIGINT", sigintHandler);

  displayBattleHeader(scenario.name, targetDir);

  const battle = await engine.run();

  process.off("SIGINT", sigintHandler);

  // Summary
  const allFindings = battle.rounds.flatMap((r) => r.findings);
  const allMitigations = battle.rounds.flatMap((r) => r.mitigations);

  if (allFindings.length === 0) {
    displayNoFindings();
  } else {
    const summary = {
      totalRounds: battle.rounds.length,
      totalFindings: allFindings.length,
      findingsBySeverity: {
        critical: allFindings.filter((f) => f.severity === "critical").length,
        high: allFindings.filter((f) => f.severity === "high").length,
        medium: allFindings.filter((f) => f.severity === "medium").length,
        low: allFindings.filter((f) => f.severity === "low").length,
      },
      totalMitigations: allMitigations.length,
      mitigationCoverage:
        allFindings.length > 0
          ? allMitigations.length / allFindings.length
          : 1,
    };

    displayBattleSummary(summary);

    // Generate and write report
    const reportContent = generateReport(battle);
    const reportPath = await writeReport(reportContent, battle.id);
    displayReportPath(reportPath);
  }

  if (battle.status === "error") {
    process.exit(1);
  }
  if (battle.status === "interrupted") {
    process.exit(1);
  }
}

async function runMetaBattle(
  targetDir: string,
  metaScenario: Scenario,
  rounds: number
): Promise<void> {
  console.log(
    `\n  Running full audit: ${metaScenario.subScenarios!.join(" -> ")}\n`
  );

  for (const subName of metaScenario.subScenarios!) {
    const subResult = await loadScenario(subName);
    if (subResult.ok) {
      console.log(`\n  --- Starting ${subName} audit ---\n`);
      await runBattle(targetDir, subResult.value, rounds);
    }
  }
}

program.parse();
