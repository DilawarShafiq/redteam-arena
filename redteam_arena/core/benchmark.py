"""
Benchmark suite -- tests detection accuracy against known-vulnerable patterns.
Calculates precision, recall, and F1 scores.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass, field

from redteam_arena.types import Finding, Severity


@dataclass
class VulnerablePattern:
    id: str
    name: str
    category: str
    severity: Severity
    language: str
    code: str
    description: str


@dataclass
class BenchmarkResult:
    suite_name: str
    total_patterns: int
    detected: int
    missed: int
    false_positives: int
    precision: float
    recall: float
    f1: float
    details: list[PatternResult] = field(default_factory=list)


@dataclass
class PatternResult:
    pattern_id: str
    pattern_name: str
    expected_severity: Severity
    detected: bool
    match_type: str  # "exact", "partial", "none"
    matched_finding: str = ""


# --- Built-in benchmark suites ---

BENCHMARK_SUITES: dict[str, list[VulnerablePattern]] = {
    "owasp-web-basic": [
        VulnerablePattern(
            id="sqli-1", name="SQL Injection (string concat)", category="sql-injection",
            severity="critical", language="python",
            code='def get_user(name):\n    query = f"SELECT * FROM users WHERE name = \'{name}\'"\n    cursor.execute(query)\n    return cursor.fetchone()',
            description="SQL injection via string concatenation",
        ),
        VulnerablePattern(
            id="sqli-2", name="SQL Injection (format string)", category="sql-injection",
            severity="critical", language="python",
            code='def search(term):\n    sql = "SELECT * FROM products WHERE name LIKE \'%" + term + "%\'"\n    db.execute(sql)',
            description="SQL injection via string concatenation in LIKE clause",
        ),
        VulnerablePattern(
            id="xss-1", name="Reflected XSS", category="xss",
            severity="high", language="javascript",
            code='app.get("/search", (req, res) => {\n  res.send(`<h1>Results for: ${req.query.q}</h1>`);\n});',
            description="Reflected XSS via unescaped query parameter in HTML",
        ),
        VulnerablePattern(
            id="xss-2", name="DOM XSS via innerHTML", category="xss",
            severity="high", language="javascript",
            code='document.getElementById("output").innerHTML = userInput;',
            description="DOM-based XSS via innerHTML assignment",
        ),
        VulnerablePattern(
            id="auth-1", name="Hardcoded JWT secret", category="auth-bypass",
            severity="critical", language="javascript",
            code='const token = jwt.sign(payload, "supersecretkey123", { expiresIn: "24h" });',
            description="Hardcoded JWT signing secret",
        ),
        VulnerablePattern(
            id="auth-2", name="No password hashing", category="auth-bypass",
            severity="high", language="python",
            code='def register(username, password):\n    db.execute("INSERT INTO users VALUES (?, ?)", (username, password))',
            description="Storing plaintext passwords in database",
        ),
        VulnerablePattern(
            id="path-1", name="Path traversal", category="path-traversal",
            severity="high", language="javascript",
            code='app.get("/file", (req, res) => {\n  const filePath = path.join(__dirname, req.query.name);\n  res.sendFile(filePath);\n});',
            description="Path traversal via unsanitized file path",
        ),
        VulnerablePattern(
            id="cmd-1", name="Command injection", category="injection",
            severity="critical", language="python",
            code='def ping(host):\n    os.system(f"ping -c 1 {host}")',
            description="OS command injection via unsanitized input",
        ),
        VulnerablePattern(
            id="ssrf-1", name="SSRF via user URL", category="ssrf",
            severity="high", language="python",
            code='def fetch_url(url):\n    response = requests.get(url)\n    return response.text',
            description="SSRF via unvalidated user-supplied URL",
        ),
        VulnerablePattern(
            id="secret-1", name="Hardcoded API key", category="secrets-exposure",
            severity="high", language="python",
            code='API_KEY = "sk-proj-abc123def456ghi789"\nclient = openai.OpenAI(api_key=API_KEY)',
            description="Hardcoded API key in source code",
        ),
    ],
    "sql-injection-focus": [
        VulnerablePattern(
            id="sqli-f1", name="SQL Injection f-string", category="sql-injection",
            severity="critical", language="python",
            code='cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")',
            description="SQL injection via f-string interpolation",
        ),
        VulnerablePattern(
            id="sqli-f2", name="SQL Injection % format", category="sql-injection",
            severity="critical", language="python",
            code='cursor.execute("SELECT * FROM items WHERE name = \'%s\'" % name)',
            description="SQL injection via % string formatting",
        ),
        VulnerablePattern(
            id="sqli-f3", name="SQL Injection .format()", category="sql-injection",
            severity="critical", language="python",
            code='query = "DELETE FROM orders WHERE id = {}".format(order_id)\ndb.execute(query)',
            description="SQL injection via .format() string method",
        ),
        VulnerablePattern(
            id="sqli-f4", name="SQL Injection in ORM raw", category="sql-injection",
            severity="high", language="python",
            code='User.objects.raw("SELECT * FROM auth_user WHERE username = \'%s\'" % username)',
            description="SQL injection in Django ORM raw query",
        ),
    ],
    "xss-focus": [
        VulnerablePattern(
            id="xss-f1", name="XSS in template", category="xss",
            severity="high", language="javascript",
            code='const html = `<div>${userData.bio}</div>`;\nres.send(html);',
            description="XSS via unescaped template literal in response",
        ),
        VulnerablePattern(
            id="xss-f2", name="XSS via document.write", category="xss",
            severity="high", language="javascript",
            code='document.write("<p>" + location.hash.slice(1) + "</p>");',
            description="DOM XSS via document.write with location.hash",
        ),
        VulnerablePattern(
            id="xss-f3", name="Stored XSS no sanitize", category="xss",
            severity="high", language="python",
            code='@app.route("/comment", methods=["POST"])\ndef add_comment():\n    comment = request.form["comment"]\n    db.execute("INSERT INTO comments VALUES (?)", (comment,))\n    return redirect("/comments")',
            description="Stored XSS via unsanitized user input stored in DB",
        ),
    ],
    "auth-focus": [
        VulnerablePattern(
            id="auth-f1", name="JWT none algorithm", category="auth-bypass",
            severity="critical", language="javascript",
            code='const decoded = jwt.verify(token, secret, { algorithms: ["HS256", "none"] });',
            description="JWT accepts 'none' algorithm allowing token forgery",
        ),
        VulnerablePattern(
            id="auth-f2", name="Timing attack on comparison", category="auth-bypass",
            severity="medium", language="python",
            code='def verify_token(provided, expected):\n    return provided == expected',
            description="Timing attack vulnerability in token comparison",
        ),
        VulnerablePattern(
            id="auth-f3", name="Missing rate limit on login", category="auth-bypass",
            severity="medium", language="python",
            code='@app.route("/login", methods=["POST"])\ndef login():\n    user = User.query.filter_by(username=request.form["username"]).first()\n    if user and user.check_password(request.form["password"]):\n        return jsonify({"token": create_token(user)})\n    return jsonify({"error": "Invalid credentials"}), 401',
            description="No rate limiting on login endpoint enables brute force",
        ),
    ],
}


def list_benchmark_suites() -> list[dict[str, str | int]]:
    """List available benchmark suites."""
    return [
        {
            "name": name,
            "patterns": len(patterns),
            "categories": len({p.category for p in patterns}),
        }
        for name, patterns in BENCHMARK_SUITES.items()
    ]


def get_benchmark_suite(name: str) -> list[VulnerablePattern] | None:
    """Get a benchmark suite by name."""
    return BENCHMARK_SUITES.get(name)


def create_benchmark_files(
    patterns: list[VulnerablePattern],
) -> tuple[str, list[str]]:
    """Create temporary files from vulnerable patterns. Returns (temp_dir, file_paths)."""
    temp_dir = tempfile.mkdtemp(prefix="redteam-bench-")
    file_paths: list[str] = []

    ext_map = {
        "python": ".py",
        "javascript": ".js",
        "typescript": ".ts",
        "go": ".go",
        "java": ".java",
        "rust": ".rs",
    }

    for pattern in patterns:
        ext = ext_map.get(pattern.language, ".txt")
        filename = f"{pattern.id}{ext}"
        filepath = os.path.join(temp_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"# Benchmark pattern: {pattern.name}\n")
            f.write(f"# Category: {pattern.category}\n")
            f.write(f"# Severity: {pattern.severity}\n\n")
            f.write(pattern.code)
            f.write("\n")
        file_paths.append(filepath)

    return temp_dir, file_paths


def evaluate_results(
    patterns: list[VulnerablePattern],
    findings: list[Finding],
) -> BenchmarkResult:
    """Evaluate detection results against known patterns."""
    details: list[PatternResult] = []
    detected_count = 0

    for pattern in patterns:
        match_type = "none"
        matched_finding = ""

        for finding in findings:
            # Check for fuzzy match on pattern ID, category, or description
            finding_text = (
                f"{finding.file_path} {finding.description} {finding.attack_vector}"
            ).lower()

            if pattern.id in finding.file_path:
                match_type = "exact"
                matched_finding = finding.id
                break
            elif pattern.category in finding_text or pattern.name.lower() in finding_text:
                match_type = "partial"
                matched_finding = finding.id
                break

        is_detected = match_type != "none"
        if is_detected:
            detected_count += 1

        details.append(
            PatternResult(
                pattern_id=pattern.id,
                pattern_name=pattern.name,
                expected_severity=pattern.severity,
                detected=is_detected,
                match_type=match_type,
                matched_finding=matched_finding,
            )
        )

    # Calculate metrics
    total = len(patterns)
    missed = total - detected_count

    # For false positives, count findings that don't match any pattern
    matched_finding_ids = {d.matched_finding for d in details if d.detected}
    false_positives = sum(
        1 for f in findings if f.id not in matched_finding_ids
    )

    precision = (
        detected_count / (detected_count + false_positives)
        if (detected_count + false_positives) > 0
        else 0.0
    )
    recall = detected_count / total if total > 0 else 0.0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return BenchmarkResult(
        suite_name="",
        total_patterns=total,
        detected=detected_count,
        missed=missed,
        false_positives=false_positives,
        precision=round(precision, 3),
        recall=round(recall, 3),
        f1=round(f1, 3),
        details=details,
    )


def format_benchmark_result(result: BenchmarkResult) -> str:
    """Format benchmark result for terminal display."""
    lines: list[str] = []
    lines.append("")
    lines.append(f"  Benchmark: {result.suite_name}")
    lines.append("  " + "=" * 40)
    lines.append(f"  Patterns:        {result.total_patterns}")
    lines.append(f"  Detected:        {result.detected}")
    lines.append(f"  Missed:          {result.missed}")
    lines.append(f"  False Positives: {result.false_positives}")
    lines.append("")
    lines.append(f"  Precision: {result.precision:.1%}")
    lines.append(f"  Recall:    {result.recall:.1%}")
    lines.append(f"  F1 Score:  {result.f1:.1%}")
    lines.append("")

    for detail in result.details:
        status = "[OK]" if detail.detected else "[MISS]"
        lines.append(f"  {status} {detail.pattern_name} ({detail.expected_severity})")
        if detail.match_type == "partial":
            lines.append("        (partial match)")

    lines.append("")
    return "\n".join(lines)
