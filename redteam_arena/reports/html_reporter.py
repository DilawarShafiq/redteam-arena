"""
Interactive HTML battle report — single-file, no external dependencies.
Features: severity charts, findings list, dark/light theme, collapsible details.
"""

from __future__ import annotations

import html

from redteam_arena.types import Battle

SEVERITY_COLORS: dict[str, str] = {
    "critical": "#dc2626",
    "high": "#ea580c",
    "medium": "#ca8a04",
    "low": "#2563eb",
}


def generate_html_report(battle: Battle) -> str:
    """Generate a self-contained HTML battle report."""
    all_findings = [f for r in battle.rounds for f in r.findings]
    all_mitigations = [m for r in battle.rounds for m in r.mitigations]

    by_severity: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in all_findings:
        by_severity[f.severity] += 1

    coverage = (
        round((len(all_mitigations) / len(all_findings)) * 100)
        if all_findings
        else 100
    )

    findings_html_parts: list[str] = []
    for i, finding in enumerate(all_findings):
        mitigation = next(
            (m for m in all_mitigations if m.finding_id == finding.id), None
        )
        snippet_html = (
            f'<pre class="code-snippet"><code>{html.escape(finding.code_snippet)}</code></pre>'
            if finding.code_snippet
            else ""
        )
        mitigation_html = ""
        if mitigation:
            mitigation_html = (
                f'<div class="mitigation">'
                f'<span class="confidence-badge confidence-{mitigation.confidence}">{mitigation.confidence}</span> '
                f"<strong>Fix:</strong> {html.escape(mitigation.proposed_fix)}"
                f'<p class="ack">{html.escape(mitigation.acknowledgment)}</p>'
                f"</div>"
            )

        findings_html_parts.append(
            f'<div class="finding" data-severity="{finding.severity}">'
            f'<div class="finding-header">'
            f'<span class="severity-badge severity-{finding.severity}">{finding.severity.upper()}</span>'
            f'<span class="finding-title">Finding {i + 1}: {html.escape(finding.description[:100])}</span>'
            f'<span class="finding-location">{html.escape(finding.file_path)}:{html.escape(finding.line_reference)}</span>'
            f"</div>"
            f'<div class="finding-body">'
            f"<p><strong>Description:</strong> {html.escape(finding.description)}</p>"
            f"<p><strong>Attack Vector:</strong> {html.escape(finding.attack_vector)}</p>"
            f"<p><strong>Round:</strong> {finding.round_number}</p>"
            f"{snippet_html}"
            f"{mitigation_html}"
            f"</div></div>"
        )

    findings_html = "\n".join(findings_html_parts)

    # Build severity chart bars
    chart_bars = ""
    for sev in ("critical", "high", "medium", "low"):
        count = by_severity[sev]
        if count > 0:
            label = {"critical": "Crit", "high": "High", "medium": "Med", "low": "Low"}[sev]
            chart_bars += f'<div class="severity-bar" style="flex:{count};background:{SEVERITY_COLORS[sev]}">{count} {label}</div>'

    # Build filter buttons
    filter_buttons = f'<button class="filter-btn active" onclick="filterFindings(\'all\')">All ({len(all_findings)})</button>'
    for sev in ("critical", "high", "medium", "low"):
        count = by_severity[sev]
        if count > 0:
            filter_buttons += f'<button class="filter-btn" onclick="filterFindings(\'{sev}\')">{sev.capitalize()} ({count})</button>'

    no_findings_msg = ""
    chart_section = ""
    if all_findings:
        chart_section = f"""
  <div class="severity-chart">{chart_bars}</div>
  <div class="findings-filter">{filter_buttons}</div>"""
    else:
        no_findings_msg = '<p style="text-align:center;color:#22c55e;font-size:1.2rem;margin:2rem 0">No vulnerabilities found.</p>'

    battle_date = battle.started_at.isoformat().split("T")[0]
    finding_color = SEVERITY_COLORS["high"] if all_findings else "#22c55e"

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RedTeam Arena - Battle Report</title>
<style>
:root {{ --bg: #0f172a; --surface: #1e293b; --border: #334155; --text: #e2e8f0; --text-muted: #94a3b8; --accent: #ef4444; }}
[data-theme="light"] {{ --bg: #f8fafc; --surface: #ffffff; --border: #e2e8f0; --text: #1e293b; --text-muted: #64748b; --accent: #dc2626; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
.container {{ max-width: 1100px; margin: 0 auto; padding: 2rem; }}
header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 2rem; border-bottom: 2px solid var(--accent); padding-bottom: 1rem; }}
h1 {{ font-size: 1.5rem; }} h1 span {{ color: var(--accent); }}
.theme-toggle {{ cursor: pointer; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 0.4rem 0.8rem; border-radius: 0.375rem; font-size: 0.85rem; }}
.meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.meta-card {{ background: var(--surface); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; }}
.meta-card .label {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 0.25rem; }}
.meta-card .value {{ font-size: 1.25rem; font-weight: 700; }}
.severity-chart {{ display: flex; gap: 0.5rem; margin-bottom: 2rem; height: 2rem; border-radius: 0.375rem; overflow: hidden; }}
.severity-bar {{ display: flex; align-items: center; justify-content: center; color: white; font-size: 0.75rem; font-weight: 700; min-width: 2rem; }}
.findings-filter {{ display: flex; gap: 0.5rem; margin-bottom: 1rem; flex-wrap: wrap; }}
.filter-btn {{ cursor: pointer; background: var(--surface); border: 1px solid var(--border); color: var(--text); padding: 0.3rem 0.7rem; border-radius: 0.375rem; font-size: 0.8rem; }}
.filter-btn.active {{ border-color: var(--accent); background: var(--accent); color: white; }}
.finding {{ background: var(--surface); border: 1px solid var(--border); border-radius: 0.5rem; margin-bottom: 1rem; overflow: hidden; }}
.finding-header {{ display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; cursor: pointer; flex-wrap: wrap; }}
.finding-body {{ padding: 0 1rem 1rem; display: none; }}
.finding.open .finding-body {{ display: block; }}
.severity-badge {{ padding: 0.15rem 0.5rem; border-radius: 0.25rem; font-size: 0.7rem; font-weight: 700; color: white; }}
.severity-critical {{ background: {SEVERITY_COLORS["critical"]}; }}
.severity-high {{ background: {SEVERITY_COLORS["high"]}; }}
.severity-medium {{ background: {SEVERITY_COLORS["medium"]}; }}
.severity-low {{ background: {SEVERITY_COLORS["low"]}; }}
.finding-title {{ flex: 1; font-weight: 600; font-size: 0.9rem; }}
.finding-location {{ font-family: monospace; font-size: 0.8rem; color: var(--text-muted); }}
.code-snippet {{ background: #0d1117; color: #e6edf3; padding: 1rem; border-radius: 0.375rem; overflow-x: auto; font-size: 0.85rem; margin: 0.75rem 0; }}
[data-theme="light"] .code-snippet {{ background: #f6f8fa; color: #24292f; }}
.mitigation {{ background: color-mix(in srgb, var(--surface) 80%, #22c55e 20%); border: 1px solid #22c55e40; border-radius: 0.375rem; padding: 0.75rem; margin-top: 0.75rem; }}
.confidence-badge {{ padding: 0.1rem 0.4rem; border-radius: 0.2rem; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; }}
.confidence-high {{ background: #22c55e; color: white; }}
.confidence-medium {{ background: #ca8a04; color: white; }}
.confidence-low {{ background: #94a3b8; color: white; }}
.ack {{ font-style: italic; color: var(--text-muted); margin-top: 0.5rem; font-size: 0.85rem; }}
footer {{ margin-top: 2rem; padding-top: 1rem; border-top: 1px solid var(--border); text-align: center; color: var(--text-muted); font-size: 0.8rem; }}
footer a {{ color: var(--accent); text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
  <header>
    <h1><span>RedTeam</span> Arena - Battle Report</h1>
    <button class="theme-toggle" onclick="toggleTheme()">Toggle Theme</button>
  </header>
  <div class="meta">
    <div class="meta-card"><div class="label">Battle ID</div><div class="value">{html.escape(battle.id)}</div></div>
    <div class="meta-card"><div class="label">Scenario</div><div class="value">{html.escape(battle.config.scenario.name)}</div></div>
    <div class="meta-card"><div class="label">Rounds</div><div class="value">{len(battle.rounds)}</div></div>
    <div class="meta-card"><div class="label">Findings</div><div class="value" style="color:{finding_color}">{len(all_findings)}</div></div>
    <div class="meta-card"><div class="label">Mitigations</div><div class="value">{coverage}%</div></div>
    <div class="meta-card"><div class="label">Status</div><div class="value">{battle.status}</div></div>
  </div>
  {chart_section}
  {no_findings_msg}
  <div id="findings">{findings_html}</div>
  <footer>
    Generated by <a href="https://github.com/DilawarShafiq/redteam-arena">RedTeam Arena</a> v0.1.0 - {battle_date}
  </footer>
</div>
<script>
function toggleTheme(){{var h=document.documentElement;h.dataset.theme=h.dataset.theme==='dark'?'light':'dark';}}
document.querySelectorAll('.finding-header').forEach(function(h){{h.addEventListener('click',function(){{h.parentElement.classList.toggle('open');}});}});
function filterFindings(sev){{document.querySelectorAll('.finding').forEach(function(f){{f.style.display=(sev==='all'||f.dataset.severity===sev)?'':'none';}});document.querySelectorAll('.filter-btn').forEach(function(b){{b.classList.remove('active');}});event.target.classList.add('active');}}
</script>
</body>
</html>"""
