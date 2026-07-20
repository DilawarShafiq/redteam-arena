"""
Scan scope disclosure -- renders what the reader actually looked at.

The file reader works to a fixed context budget, so a scan is often partial.
Every report that a human might act on has to say so; otherwise a review of 2%
of a codebase reads exactly like a review of all of it.
"""

from __future__ import annotations

from redteam_arena.types import ScanScope

_MAX_LISTED = 10


def format_scan_scope(scope: ScanScope | None) -> list[str]:
    """Render a scope disclosure block as markdown lines."""
    if scope is None:
        return []

    lines: list[str] = ["### Scan Scope", ""]

    kb_read = scope.bytes_read / 1024
    budget_kb = scope.max_total_size / 1024
    lines.append(f"- Files examined: **{scope.files_read}**")
    lines.append(f"- Source read: **{kb_read:.1f} KB** of a {budget_kb:.0f} KB context budget")

    if not scope.is_partial:
        lines.append("- Coverage: the reader reached every matching file in the target.")
        lines.append("")
        return lines

    lines.append("")
    lines.append("> ⚠️ **This scan was partial.** Findings cover only the files listed as")
    lines.append("> examined. Anything not read cannot have been assessed, so an absence of")
    lines.append("> findings in the remainder means nothing.")
    lines.append("")

    if scope.budget_exhausted:
        lines.append(
            f"- The {budget_kb:.0f} KB context budget was exhausted, so the walk stopped early. "
            "Files are visited in alphabetical order, so later directories may be untouched."
        )
    if scope.skipped_over_budget:
        lines.append(f"- Skipped, would not fit in remaining budget: **{len(scope.skipped_over_budget)}**")
        lines.extend(_bullet_list(scope.skipped_over_budget))
    if scope.skipped_too_large:
        lines.append(f"- Skipped, exceeded the per-file size cap: **{len(scope.skipped_too_large)}**")
        lines.extend(_bullet_list(scope.skipped_too_large))

    lines.append("")
    return lines


def _bullet_list(paths: list[str]) -> list[str]:
    """Indented bullets, truncated so a huge skip list cannot swamp the report."""
    shown = [f"  - `{p}`" for p in paths[:_MAX_LISTED]]
    if len(paths) > _MAX_LISTED:
        shown.append(f"  - ...and {len(paths) - _MAX_LISTED} more")
    return shown
