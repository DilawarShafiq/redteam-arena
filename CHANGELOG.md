# Changelog

All notable changes to RedTeam Arena are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added
- **The scan budget is configurable.** The reader stopped at a fixed 100 KB and could not be raised, so large codebases were only ever partially covered. `--max-scan-kb` (and `maxScanKb` in `.redteamarena.yml`) now sets the budget; raising it also lifts the old 64 KB per-file cap so large single files are no longer silently dropped. This is a single pass bounded by the model's context window — there is no multi-pass API-cost multiplier. Combined with the scope disclosure added in 0.0.5, coverage is now both adjustable and always stated.

### Fixed
- **Scan scope was dropped from the returned battle.** `BattleEngine.get_battle()` did not copy `scan_scope`, so the coverage disclosure never reached the reporters that consume the returned object. Now carried through.
- **SARIF output now works with GitHub code scanning.** Three defects made it churn or fail to map: rule IDs were an MD5 of the finding's prose and result fingerprints included the description, so every run produced new IDs and GitHub re-created every alert (dismissals never stuck); and the `uriBaseId` was the malformed `%SRCROOT%` with paths relative to the scanned directory rather than the repository root, so results could fail to map onto files in the commit. Rule IDs are now `redteam-arena/<scenario>` and fingerprints are location-based, both stable across runs; paths are resolved relative to the enclosing git repo root. Adds 12 tests to a reporter whose function bodies previously had no coverage.
- **`--auto-fix` no longer modifies your repository by default, and its git handling is safe.** It advertised "applies Blue Agent mitigations directly" but never edited source — it wrote markdown proposals, created a branch per finding, and left the repo checked out on the last one. Worse, no git command's exit code was checked, so a failed `checkout -b` did not stop the run and the following commit could land on the current branch (e.g. `main`). Now: writing proposals is the default and touches no git state; committing to per-finding branches is opt-in via `--auto-fix-branch`; every git call is checked; the original branch is always restored; and it refuses to run on a dirty tree or a non-repo. The flag and report wording no longer claim fixes were applied. Adds 12 tests to a module that previously had none.

## [0.0.5] — 2026-07-21

A correctness release. No new scenarios or features: everything here either
fixes something that was broken or removes a claim the tool could not support.

### Fixed
- **The agents are no longer tied to Claude.** The Red, Blue and Auditor agents each named a Claude model in their request options, which overrode whatever provider the user selected — so `--provider openai` sent a Claude model string to OpenAI, and `--model` was discarded entirely. Three of the four advertised providers were non-functional for battles. Agents now send no model at all, leaving each adapter to apply its own default (`gpt-4o`, `gemini-2.0-flash`, `llama3.2`, `claude-sonnet-4`), and forwarding `--model` verbatim when given. The Auditor agent additionally defaulted to a superseded Claude 3.7 model.
- `redteam --version` reported a hardcoded `0.0.4` from a third copy of the version string in `cli.py`; it now tracks `__version__`.
- **`Dockerfile` and `.env` files were never read** — `os.path.splitext` returns an empty extension for extensionless names and bare dotfiles, so neither could match the extension allowlist. The secrets-exposure scenario could not see `.env` files at all. Matching is now by filename as well as extension, including suffixed variants such as `Dockerfile.prod`.
- **CI was red on `main`**, which blocked the `publish` job (`needs: test`) and therefore all releases: a `ruff` import-order error introduced in 0.0.4, a version assertion pinned to `0.0.1` against a `0.0.4` package, and two `mypy` assignment errors in `cli.py`.
- SARIF reports declared a hardcoded `semanticVersion` of `0.1.0` regardless of the installed version.

### Added
- **Finding location validation** — every model-reported finding is now checked against the source that was actually scanned: the path must resolve to a scanned file, the line must fall within it, and any quoted snippet must appear in it. Results are recorded on `Finding.verification` as `verified`, `unverified`, `not_in_scope` or `unchecked`. Findings are annotated rather than dropped, since a mislocated finding may still describe a real issue.
- **Scan scope disclosure** — the reader stops at a fixed context budget, so scans are frequently partial. `ScanScope` now records files read, bytes read, budget exhaustion and skipped files, and reports render it with an explicit warning when coverage is incomplete.
- **OWASP Agentic Top 10 (2026) mapping** — the ten agentic scenarios declare their `owasp_asi` ID, and `redteam list` reports coverage against the standard.

### Changed
- **The compliance report no longer presents itself as an audit.** It was titled "ENTERPRISE COMPLIANCE AUDIT REPORT / Independent Cybersecurity & Compliance Assessment", carried report IDs and remediation SLAs, and printed "no significant control gaps were identified" when the model may never have read the code. SOC 2 (SSAE 18 / AT-C 205), ISO 27001 (ISO/IEC 17021-1) and HITRUST all reserve issuance for accredited third parties. It is now "Control Gap Analysis — Automated Pre-Audit Input, Unverified", carries a disclaimer naming that requirement, frames SLAs as suggested triage priorities, and treats an empty run as inconclusive rather than as a pass.
- CI lints `tests/` in addition to the package.
- Dependabot updates are grouped per ecosystem and run monthly rather than weekly.

---

## [0.0.4] — 2026-02-28

### Added
- **APT Threat Actor Persona** — Overhauled the Red Agent system prompt to think like an elite black-hat operator (e.g., ALPHV/BlackCat), focusing on "Living off the Land" (LotL) and chained attack paths.
- **Strict Zero-Trust Auditor** — Updated the Auditor Agent to automatically flag missing MFA, missing RBAC, and session vulnerabilities as Critical/High failures.
- **APT Scenario** (`apt-advanced-persistent-threat`) — A new scenario specifically designed to hunt for MFA bypasses, Kerberos/AD token exploitation, and lateral movement.
- **Infrastructure as Code Scenario** (`infrastructure-as-code`) — A new scenario for auditing Terraform, Kubernetes, Docker, and CI/CD pipelines for cloud misconfigurations.

---

## [0.0.3] — 2026-02-28

### Changed
- Documentation only — README updated to describe the enterprise and healthcare capabilities introduced in 0.0.2. No code changes.

---

## [0.0.2] — 2026-02-28

### Added
- **Enterprise Auditor Agent** (`--agent-mode auditor`) — A specialized agent for compliance and architectural audits.
- **Enterprise Compliance Scenarios** — 8 high-end regulatory scenarios including ISO 42001 (AI), SOC 2, FedRAMP, HIPAA/HITECH, HITRUST CSF, EPCS DEA, PCI-DSS, and GDPR/CCPA.
- **Compliance Reporter** (`--format compliance`) — Generates Markdown reports grouped by severity. (Retitled in a later release; see Unreleased.)
- **Mock LLM Support** (`--mock-llm`) — For dry runs, CI testing, and fast demonstrations.

### Fixed
- Resolved 25 mypy type errors and remaining CI blockers ahead of public launch.
- `.claude/settings.local.json` is gitignored to prevent API key exposure.

---

## [0.0.1] — 2026-02-27

First public release.

### Added

- **Battle engine** — async Red Agent / Blue Agent loop with multi-round support and graceful interrupt handling
- **7 CLI commands** — `battle`, `list`, `watch`, `serve`, `benchmark`, `history`, `dashboard`
- **33 built-in scenarios** covering OWASP Top 10, AI safety (prompt injection, data poisoning, agent hijacking, excessive agency, memory poisoning, tool misuse, rogue agents, and more)
- **4 report formats** — Markdown, JSON, SARIF (GitHub Code Scanning compatible), HTML
- **Multi-provider support** — Claude (default), OpenAI, Gemini, Ollama
- **Diff mode** — `--diff` flag to scan only git-changed files
- **CI integration** — `--fail-on <severity>` exit code for pipeline gating
- **PR comments** — `--pr-comment` to post findings directly on GitHub PRs
- **Advanced analysis** — `--analyze` for cross-cutting vulnerability patterns
- **Auto-fix** — `--auto-fix` to generate fix suggestions as a branch
- **Watch mode** — continuous re-scan on file changes
- **Benchmark suite** — detection accuracy measurement across scenario sets
- **Battle history** — persistent store with trends and regression analysis
- **HTML dashboard** — rich visual overview of all past battles
- **REST + WebSocket API server** — programmatic access via `pip install redteam-arena[server]`
- **Programmatic Python API** — full import surface for embedding in other tools
- **Config file support** — `.redteamarena.yml` for per-project settings

[0.0.4]: https://github.com/DilawarShafiq/redteam-arena/releases/tag/v0.0.4
[0.0.3]: https://github.com/DilawarShafiq/redteam-arena/releases/tag/v0.0.3
[0.0.1]: https://github.com/DilawarShafiq/redteam-arena/releases/tag/v0.0.1
