"""
HTML dashboard generator -- battle history, trends, and statistics.
"""

from __future__ import annotations

import html
import json
import os

from redteam_arena.core.battle_store import BattleRecord, BattleTrend


def generate_dashboard(
    records: list[BattleRecord],
    trends: list[BattleTrend],
) -> str:
    """Generate a self-contained HTML dashboard."""
    total_battles = len(records)
    total_findings = sum(r.total_findings for r in records)
    avg_coverage = (
        sum(r.mitigation_coverage for r in records) / total_battles
        if total_battles > 0
        else 0
    )

    # Build records JSON for embedded chart data
    records_json = json.dumps([
        {
            "id": r.id,
            "scenario": r.scenario,
            "status": r.status,
            "findings": r.total_findings,
            "mitigations": r.total_mitigations,
            "coverage": round(r.mitigation_coverage * 100),
            "date": r.started_at[:10],
            "critical": r.findings_by_severity.get("critical", 0),
            "high": r.findings_by_severity.get("high", 0),
            "medium": r.findings_by_severity.get("medium", 0),
            "low": r.findings_by_severity.get("low", 0),
        }
        for r in records
    ])

    trend_rows = ""
    for t in trends:
        trend_rows += (
            f'<tr><td>{t.period}</td><td>{t.total_battles}</td>'
            f'<td>{t.total_findings}</td><td>{round(t.avg_coverage * 100)}%</td>'
            f'<td>{t.by_severity.get("critical", 0)}</td>'
            f'<td>{t.by_severity.get("high", 0)}</td></tr>'
        )

    battle_rows = ""
    for r in records[:50]:
        status_class = "ok" if r.status == "completed" else "err"
        battle_rows += (
            f'<tr class="{status_class}">'
            f'<td>{html.escape(r.id)}</td>'
            f'<td>{html.escape(r.scenario)}</td>'
            f'<td>{r.total_findings}</td>'
            f'<td>{round(r.mitigation_coverage * 100)}%</td>'
            f'<td>{r.status}</td>'
            f'<td>{r.started_at[:19]}</td>'
            f'</tr>'
        )

    return f"""<!DOCTYPE html>
<html lang="en" data-theme="dark">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RedTeam Arena Dashboard</title>
<style>
:root {{ --bg: #0f172a; --surface: #1e293b; --border: #334155; --text: #e2e8f0; --accent: #ef4444; }}
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, sans-serif; background: var(--bg); color: var(--text); }}
.container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
h1 {{ font-size: 1.5rem; margin-bottom: 1.5rem; }} h1 span {{ color: var(--accent); }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-bottom: 2rem; }}
.stat {{ background: var(--surface); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; text-align: center; }}
.stat .label {{ font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; }}
.stat .value {{ font-size: 1.5rem; font-weight: 700; margin-top: 0.25rem; }}
table {{ width: 100%; border-collapse: collapse; margin-bottom: 2rem; }}
th, td {{ padding: 0.5rem 0.75rem; text-align: left; border-bottom: 1px solid var(--border); font-size: 0.85rem; }}
th {{ background: var(--surface); font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em; }}
tr.ok td:nth-child(5) {{ color: #22c55e; }}
tr.err td:nth-child(5) {{ color: var(--accent); }}
h2 {{ font-size: 1.1rem; margin: 1.5rem 0 0.75rem; }}
footer {{ margin-top: 2rem; text-align: center; color: #64748b; font-size: 0.8rem; }}
footer a {{ color: var(--accent); text-decoration: none; }}
</style>
</head>
<body>
<div class="container">
  <h1><span>RedTeam</span> Arena Dashboard</h1>
  <div class="stats">
    <div class="stat"><div class="label">Total Battles</div><div class="value">{total_battles}</div></div>
    <div class="stat"><div class="label">Total Findings</div><div class="value" style="color:#ea580c">{total_findings}</div></div>
    <div class="stat"><div class="label">Avg Coverage</div><div class="value">{round(avg_coverage * 100)}%</div></div>
    <div class="stat"><div class="label">Scenarios Used</div><div class="value">{len({r.scenario for r in records})}</div></div>
  </div>

  <h2>Trends</h2>
  <table>
    <thead><tr><th>Period</th><th>Battles</th><th>Findings</th><th>Coverage</th><th>Critical</th><th>High</th></tr></thead>
    <tbody>{trend_rows}</tbody>
  </table>

  <h2>Recent Battles</h2>
  <table>
    <thead><tr><th>ID</th><th>Scenario</th><th>Findings</th><th>Coverage</th><th>Status</th><th>Date</th></tr></thead>
    <tbody>{battle_rows}</tbody>
  </table>

  <footer>
    <a href="https://github.com/DilawarShafiq/redteam-arena">RedTeam Arena</a> v0.1.0
  </footer>
</div>
<script>const data={records_json};</script>
</body>
</html>"""


async def write_dashboard(
    records: list[BattleRecord],
    trends: list[BattleTrend],
    output_path: str = "",
) -> str:
    """Generate and write the dashboard HTML file."""
    content = generate_dashboard(records, trends)
    path = output_path or os.path.join(os.getcwd(), "redteam-dashboard.html")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path
