/**
 * Terminal display — chalk-based formatters for battle output.
 * Handles real-time streaming display and summary formatting.
 */

import chalk from "chalk";
import type {
  Finding,
  Mitigation,
  BattleSummary,
  Severity,
} from "./types.js";

const SEVERITY_COLORS: Record<Severity, (s: string) => string> = {
  critical: chalk.bgRed.white.bold,
  high: chalk.red.bold,
  medium: chalk.yellow,
  low: chalk.gray,
};

const SEVERITY_LABELS: Record<Severity, string> = {
  critical: "CRITICAL",
  high: "HIGH",
  medium: "MEDIUM",
  low: "LOW",
};

export function displayBattleHeader(
  scenario: string,
  targetDir: string
): void {
  console.log("");
  console.log(
    chalk.bold.white(
      "  REDTEAM ARENA v0.1.0"
    )
  );
  console.log(
    chalk.dim(
      `  Scenario: ${scenario} | Target: ${targetDir}`
    )
  );
  console.log(chalk.dim("  " + "=".repeat(50)));
  console.log("");
}

export function displayRoundStart(roundNumber: number, totalRounds: number): void {
  console.log(
    chalk.bold.white(`\n  Round ${roundNumber}/${totalRounds}`)
  );
  console.log(chalk.dim("  " + "-".repeat(40)));
}

export function displayRedChunk(chunk: string): void {
  process.stdout.write(chalk.red(chunk));
}

export function displayBlueChunk(chunk: string): void {
  process.stdout.write(chalk.blue(chunk));
}

export function displayRedHeader(): void {
  console.log("");
  console.log(chalk.red.bold("  RED AGENT (Attacker):"));
  console.log("");
  process.stdout.write("  ");
}

export function displayBlueHeader(): void {
  console.log("");
  console.log(chalk.blue.bold("  BLUE AGENT (Defender):"));
  console.log("");
  process.stdout.write("  ");
}

export function displayAgentDone(): void {
  console.log("");
}

export function displayFinding(finding: Finding): void {
  const severityBadge = SEVERITY_COLORS[finding.severity](
    ` ${SEVERITY_LABELS[finding.severity]} `
  );
  console.log(
    chalk.red(
      `  ${severityBadge} ${finding.filePath}:${finding.lineReference}`
    )
  );
  console.log(chalk.red(`    ${finding.description}`));
  if (finding.attackVector) {
    console.log(chalk.red.dim(`    Attack: ${finding.attackVector}`));
  }
}

export function displayMitigation(mitigation: Mitigation): void {
  const confBadge =
    mitigation.confidence === "high"
      ? chalk.green("[HIGH]")
      : mitigation.confidence === "medium"
        ? chalk.yellow("[MED]")
        : chalk.gray("[LOW]");
  console.log(chalk.blue(`  ${confBadge} ${mitigation.acknowledgment}`));
  console.log(chalk.blue(`    Fix: ${mitigation.proposedFix}`));
}

export function displayRoundEnd(
  roundNumber: number,
  findingCount: number,
  mitigationCount: number
): void {
  console.log(
    chalk.dim(
      `\n  Round ${roundNumber}: ${findingCount} finding(s), ${mitigationCount} mitigation(s)`
    )
  );
}

export function displayBattleSummary(summary: BattleSummary): void {
  console.log("");
  console.log(chalk.bold.white("  " + "=".repeat(50)));
  console.log(chalk.bold.white("  Battle Report Summary"));
  console.log(chalk.bold.white("  " + "=".repeat(50)));
  console.log("");
  console.log(
    chalk.white(`  Rounds: ${summary.totalRounds}  |  Vulnerabilities: ${summary.totalFindings}`)
  );

  const { findingsBySeverity } = summary;
  const severityLine = [
    findingsBySeverity.critical > 0
      ? chalk.bgRed.white.bold(` Critical: ${findingsBySeverity.critical} `)
      : null,
    findingsBySeverity.high > 0
      ? chalk.red(`High: ${findingsBySeverity.high}`)
      : null,
    findingsBySeverity.medium > 0
      ? chalk.yellow(`Medium: ${findingsBySeverity.medium}`)
      : null,
    findingsBySeverity.low > 0
      ? chalk.gray(`Low: ${findingsBySeverity.low}`)
      : null,
  ]
    .filter(Boolean)
    .join("  |  ");

  if (severityLine) {
    console.log(`  ${severityLine}`);
  }

  const coverage = Math.round(summary.mitigationCoverage * 100);
  console.log(
    chalk.blue(
      `  Mitigations proposed: ${summary.totalMitigations}/${summary.totalFindings} (${coverage}%)`
    )
  );
}

export function displayReportPath(path: string): void {
  console.log("");
  console.log(chalk.green.bold(`  Full report: ${path}`));
  console.log("");
}

export function displayError(message: string): void {
  console.error(chalk.red.bold(`\n  Error: ${message}\n`));
}

export function displayWarning(message: string): void {
  console.log(chalk.yellow(`  Warning: ${message}`));
}

export function displayNoFindings(): void {
  console.log("");
  console.log(chalk.green.bold("  No vulnerabilities found!"));
  console.log(
    chalk.green("  The codebase looks clean for this scenario.")
  );
  console.log("");
}

export function displayInterrupted(): void {
  console.log("");
  console.log(chalk.yellow.bold("  Battle interrupted."));
}
