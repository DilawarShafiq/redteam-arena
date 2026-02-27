"""
Advanced analysis -- data flow tracing, vulnerability chains,
dependency scanning, and language-specific deep patterns.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from redteam_arena.types import FileEntry, Finding, Severity


@dataclass
class VulnerabilityChain:
    id: str
    findings: list[str]  # finding IDs
    description: str
    combined_severity: Severity
    attack_path: list[str]


@dataclass
class DataFlowTrace:
    source: str
    transforms: list[str]
    sink: str
    file_path: str
    tainted: bool


@dataclass
class DependencyRisk:
    package: str
    risk: str
    severity: Severity
    file_path: str


@dataclass
class DeepPatternMatch:
    pattern_name: str
    file_path: str
    line: int
    code: str
    severity: Severity
    description: str


@dataclass
class AdvancedAnalysisResult:
    chains: list[VulnerabilityChain] = field(default_factory=list)
    data_flows: list[DataFlowTrace] = field(default_factory=list)
    dependency_risks: list[DependencyRisk] = field(default_factory=list)
    deep_patterns: list[DeepPatternMatch] = field(default_factory=list)


# --- Risky packages ---

RISKY_PACKAGES: dict[str, tuple[str, Severity]] = {
    "node-serialize": ("Known deserialization RCE vulnerability", "critical"),
    "serialize-javascript": ("Potential code injection via serialization", "high"),
    "eval": ("Direct code execution from strings", "critical"),
    "shell-quote": ("Command injection in older versions", "high"),
    "pickle": ("Python pickle deserialization is unsafe", "critical"),
    "yaml.load": ("Unsafe YAML loading allows code execution", "high"),
    "marshal": ("Python marshal is not safe for untrusted data", "high"),
    "exec": ("Direct code execution", "critical"),
    "child_process": ("OS command execution - verify inputs", "medium"),
    "subprocess": ("OS command execution - verify inputs", "medium"),
}

# --- Deep patterns per language ---

DEEP_PATTERNS: dict[str, list[tuple[str, str, Severity, str]]] = {
    "typescript": [
        (r"eval\s*\(", "eval() usage", "critical", "Direct code execution via eval()"),
        (r"__proto__\s*[=\[]", "Prototype pollution", "high", "Prototype chain manipulation"),
        (r"new\s+RegExp\s*\([^)]*\+", "ReDoS risk", "medium", "User input in RegExp constructor"),
        (r"csrf.*disable|csrf.*false", "CSRF disabled", "high", "CSRF protection disabled"),
        (r'algorithms.*"none"', "JWT none algorithm", "critical", "JWT accepts none algorithm"),
        (r"JSON\.parse\s*\(\s*(?:req|request)", "Unsafe JSON parse", "medium", "Unvalidated JSON parsing of user input"),
        (r'(?:password|secret|key|token)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret", "high", "Secret value hardcoded in source"),
        (r'Access-Control-Allow-Origin.*\*', "CORS wildcard", "medium", "Permissive CORS configuration"),
    ],
    "javascript": [
        (r"eval\s*\(", "eval() usage", "critical", "Direct code execution via eval()"),
        (r"__proto__\s*[=\[]", "Prototype pollution", "high", "Prototype chain manipulation"),
        (r"innerHTML\s*=", "innerHTML assignment", "high", "DOM XSS via innerHTML"),
        (r"document\.write\s*\(", "document.write", "high", "DOM manipulation via document.write"),
        (r'(?:password|secret|key|token)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret", "high", "Secret value hardcoded in source"),
    ],
    "python": [
        (r"pickle\.loads?\s*\(", "Unsafe pickle", "critical", "Pickle deserialization of untrusted data"),
        (r"yaml\.load\s*\([^)]*(?!Loader)", "Unsafe YAML load", "high", "yaml.load without SafeLoader"),
        (r"os\.system\s*\(", "OS command execution", "critical", "Direct OS command execution"),
        (r"subprocess\.(?:call|run|Popen)\s*\(.*shell\s*=\s*True", "Shell injection", "critical", "Subprocess with shell=True"),
        (r"exec\s*\(", "exec() usage", "critical", "Dynamic code execution via exec()"),
        (r"eval\s*\(", "eval() usage", "critical", "Dynamic code evaluation"),
        (r'(?:password|secret|key|token)\s*[=:]\s*["\'][^"\']{8,}["\']', "Hardcoded secret", "high", "Secret value hardcoded in source"),
        (r"__import__\s*\(", "Dynamic import", "medium", "Dynamic module import"),
    ],
    "go": [
        (r"unsafe\.Pointer", "Unsafe pointer", "high", "Use of unsafe.Pointer bypasses type safety"),
        (r"TLSClientConfig.*InsecureSkipVerify.*true", "TLS skip verify", "high", "TLS certificate verification disabled"),
        (r'exec\.Command\s*\(.*\+', "Command injection risk", "high", "User input in exec.Command"),
    ],
    "java": [
        (r"ObjectInputStream", "Deserialization", "critical", "Java deserialization of untrusted data"),
        (r"Runtime\.getRuntime\(\)\.exec", "Command execution", "critical", "OS command execution via Runtime.exec"),
        (r"PreparedStatement.*\+", "SQL injection risk", "high", "String concatenation in SQL query"),
    ],
    "rust": [
        (r"unsafe\s*\{", "Unsafe block", "medium", "Unsafe Rust block - review carefully"),
    ],
}


def analyze_vulnerability_chains(
    findings: list[Finding],
) -> list[VulnerabilityChain]:
    """Identify multi-finding vulnerability chains."""
    chains: list[VulnerabilityChain] = []

    # Group findings by file
    by_file: dict[str, list[Finding]] = {}
    for f in findings:
        by_file.setdefault(f.file_path, []).append(f)

    chain_id = 0
    for file_path, file_findings in by_file.items():
        if len(file_findings) < 2:
            continue

        # Check for related vulnerability chains
        severities = [f.severity for f in file_findings]
        has_critical = "critical" in severities
        has_high = "high" in severities

        if has_critical or (has_high and len(file_findings) >= 2):
            chain_id += 1
            combined: Severity = "critical" if has_critical else "high"
            chains.append(
                VulnerabilityChain(
                    id=f"chain-{chain_id}",
                    findings=[f.id for f in file_findings],
                    description=(
                        f"Multiple vulnerabilities in {file_path} "
                        f"may form an attack chain"
                    ),
                    combined_severity=combined,
                    attack_path=[
                        f"{f.description[:50]} ({f.severity})"
                        for f in file_findings
                    ],
                )
            )

    return chains


def trace_data_flows(files: list[FileEntry]) -> list[DataFlowTrace]:
    """Trace data flow from user input sources to dangerous sinks."""
    traces: list[DataFlowTrace] = []

    source_patterns = [
        r"req(?:uest)?\.(?:query|body|params|headers|cookies)",
        r"request\.(?:form|args|json|data|files)",
        r"input\s*\(",
        r"sys\.argv",
        r"os\.environ",
    ]

    sink_patterns = [
        r"\.execute\s*\(",
        r"\.query\s*\(",
        r"eval\s*\(",
        r"exec\s*\(",
        r"os\.system\s*\(",
        r"innerHTML\s*=",
        r"document\.write\s*\(",
        r"res\.send\s*\(",
        r"\.sendFile\s*\(",
    ]

    for file_entry in files:
        lines = file_entry.content.split("\n")
        sources_found: list[str] = []
        sinks_found: list[str] = []

        for i, line in enumerate(lines):
            for sp in source_patterns:
                if re.search(sp, line):
                    sources_found.append(f"L{i + 1}: {line.strip()[:60]}")
            for sk in sink_patterns:
                if re.search(sk, line):
                    sinks_found.append(f"L{i + 1}: {line.strip()[:60]}")

        # If both sources and sinks exist in the same file, create a trace
        for source in sources_found:
            for sink in sinks_found:
                traces.append(
                    DataFlowTrace(
                        source=source,
                        transforms=[],
                        sink=sink,
                        file_path=file_entry.path,
                        tainted=True,
                    )
                )

    return traces


def scan_dependencies(files: list[FileEntry]) -> list[DependencyRisk]:
    """Scan for known risky packages in dependency files."""
    risks: list[DependencyRisk] = []
    dep_files = {
        "package.json",
        "requirements.txt",
        "Pipfile",
        "pyproject.toml",
        "Cargo.toml",
        "go.mod",
        "Gemfile",
    }

    for file_entry in files:
        filename = os.path.basename(file_entry.path)
        if filename not in dep_files:
            continue

        content_lower = file_entry.content.lower()
        for pkg, (risk_desc, severity) in RISKY_PACKAGES.items():
            if pkg.lower() in content_lower:
                risks.append(
                    DependencyRisk(
                        package=pkg,
                        risk=risk_desc,
                        severity=severity,
                        file_path=file_entry.path,
                    )
                )

    return risks


def scan_deep_patterns(files: list[FileEntry]) -> list[DeepPatternMatch]:
    """Run language-specific deep pattern analysis."""
    matches: list[DeepPatternMatch] = []

    ext_to_lang = {
        ".ts": "typescript", ".tsx": "typescript",
        ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript",
        ".py": "python", ".pyw": "python",
        ".go": "go",
        ".java": "java", ".kt": "java",
        ".rs": "rust",
    }

    for file_entry in files:
        ext = os.path.splitext(file_entry.path)[1].lower()
        lang = ext_to_lang.get(ext)
        if not lang:
            continue

        patterns = DEEP_PATTERNS.get(lang, [])
        lines = file_entry.content.split("\n")

        for i, line in enumerate(lines):
            for regex, name, severity, description in patterns:
                if re.search(regex, line, re.IGNORECASE):
                    matches.append(
                        DeepPatternMatch(
                            pattern_name=name,
                            file_path=file_entry.path,
                            line=i + 1,
                            code=line.strip()[:120],
                            severity=severity,
                            description=description,
                        )
                    )

    return matches


async def run_advanced_analysis(
    files: list[FileEntry],
    findings: list[Finding],
) -> AdvancedAnalysisResult:
    """Run all advanced analysis modules."""
    return AdvancedAnalysisResult(
        chains=analyze_vulnerability_chains(findings),
        data_flows=trace_data_flows(files),
        dependency_risks=scan_dependencies(files),
        deep_patterns=scan_deep_patterns(files),
    )


def format_advanced_analysis(result: AdvancedAnalysisResult) -> str:
    """Format advanced analysis result for terminal display."""
    lines: list[str] = []
    lines.append("")
    lines.append("  Advanced Analysis")
    lines.append("  " + "=" * 40)

    if result.chains:
        lines.append(f"\n  Vulnerability Chains: {len(result.chains)}")
        for chain in result.chains:
            lines.append(f"    [{chain.combined_severity.upper()}] {chain.description}")
            for step in chain.attack_path:
                lines.append(f"      -> {step}")

    if result.data_flows:
        lines.append(f"\n  Data Flow Traces: {len(result.data_flows)}")
        for flow in result.data_flows[:10]:
            lines.append(f"    {flow.file_path}: {flow.source} -> {flow.sink}")

    if result.dependency_risks:
        lines.append(f"\n  Dependency Risks: {len(result.dependency_risks)}")
        for risk in result.dependency_risks:
            lines.append(f"    [{risk.severity.upper()}] {risk.package}: {risk.risk}")

    if result.deep_patterns:
        lines.append(f"\n  Deep Pattern Matches: {len(result.deep_patterns)}")
        for match in result.deep_patterns[:20]:
            lines.append(
                f"    [{match.severity.upper()}] {match.file_path}:{match.line} "
                f"- {match.pattern_name}"
            )

    if not any([result.chains, result.data_flows, result.dependency_risks, result.deep_patterns]):
        lines.append("  No advanced issues detected.")

    lines.append("")
    return "\n".join(lines)
