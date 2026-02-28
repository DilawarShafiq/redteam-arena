# Changelog

All notable changes to RedTeam Arena are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [0.0.2] — 2026-02-28

### Added
- **Enterprise Auditor Agent** (`--agent-mode auditor`) — A specialized agent for compliance and architectural audits.
- **Enterprise Compliance Scenarios** — 8 high-end regulatory scenarios including ISO 42001 (AI), SOC 2, FedRAMP, HIPAA/HITECH, HITRUST CSF, EPCS DEA, PCI-DSS, and GDPR/CCPA.
- **Compliance Reporter** (`--format compliance`) — Generates professional enterprise-grade Markdown reports with SLAs and Risk Postures.
- **Mock LLM Support** (`--mock-llm`) — For dry runs, CI testing, and fast demonstrations.

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

[0.0.2]: https://github.com/DilawarShafiq/redteam-arena/releases/tag/v0.0.2
[0.0.1]: https://github.com/DilawarShafiq/redteam-arena/releases/tag/v0.0.1
