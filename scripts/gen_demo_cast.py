"""
Generate a realistic asciinema v2 cast file for RedTeam Arena demo GIF.
Uses exact ANSI sequences that `rich` emits, matching display.py output.

Usage:
    python scripts/gen_demo_cast.py > demo.cast
    agg demo.cast demo.gif --theme monokai --font-size 14
"""

from __future__ import annotations
import json
import sys

ESC = "\u001b"
RESET = f"{ESC}[0m"

# Rich-equivalent styles
BOLD_WHITE   = f"{ESC}[1;97m"
BOLD_RED     = f"{ESC}[1;31m"
BOLD_BLUE    = f"{ESC}[1;34m"
BOLD_GREEN   = f"{ESC}[1;32m"
BOLD_YELLOW  = f"{ESC}[1;33m"
DIM          = f"{ESC}[2m"
RED          = f"{ESC}[31m"
BLUE         = f"{ESC}[34m"
GREEN        = f"{ESC}[32m"
YELLOW       = f"{ESC}[33m"
# Bold white on red background (CRITICAL badge)
CRIT_BADGE   = f"{ESC}[1;97;41m"
# Bold red (HIGH badge)
HIGH_BADGE   = f"{ESC}[1;31m"
MED_BADGE    = f"{ESC}[33m"

WIDTH  = 110
HEIGHT = 36


def cast_header() -> str:
    meta = {
        "version": 2,
        "width":   WIDTH,
        "height":  HEIGHT,
        "timestamp": 1740614400,
        "title": "RedTeam Arena — AI vs AI security testing",
        "env": {"TERM": "xterm-256color", "SHELL": "/bin/bash"},
    }
    return json.dumps(meta)


# (time_offset_seconds, text)
EVENTS: list[tuple[float, str]] = []


def o(t: float, text: str) -> None:
    EVENTS.append((t, text))


def line(t: float, text: str, style: str = "", end: str = "\r\n") -> float:
    o(t, f"{style}{text}{RESET if style else ''}{end}")
    return t + 0.04


def blank(t: float) -> float:
    o(t, "\r\n")
    return t + 0.03


def stream(t: float, words: list[tuple[str, str]], style: str, prefix: str = "  ") -> float:
    """Simulate streaming text word by word."""
    o(t, prefix)
    t += 0.05
    for word, gap_after in words:
        o(t, f"{style}{word}{RESET} ")
        t += 0.06 + (0.08 if gap_after == "long" else 0.0)
    o(t, "\r\n")
    return t + 0.1


def build_events() -> None:
    t = 0.3

    # Shell prompt + command
    o(t, f"{GREEN}❯{RESET} ")
    t += 0.4
    cmd = "redteam-arena battle ./webapp --scenario prompt-injection --rounds 3"
    for ch in cmd:
        o(t, ch)
        t += 0.035
    o(t, "\r\n")
    t += 0.6

    # ── Header ──────────────────────────────────────────────────────────────
    o(t, "\r\n"); t += 0.05
    t = line(t, "  REDTEAM ARENA v0.0.1", BOLD_WHITE)
    t = line(t, "  Scenario: prompt-injection  |  Target: ./webapp", DIM)
    t = line(t, "  " + "═" * 54, DIM)
    t = blank(t)

    # ── ROUND 1 ──────────────────────────────────────────────────────────────
    t = blank(t)
    t = line(t, "  Round 1/3", BOLD_WHITE)
    t = line(t, "  " + "─" * 40, DIM)
    t += 0.3

    # RED header
    t = blank(t)
    t = line(t, "  RED AGENT (Attacker):", BOLD_RED)
    t = blank(t)
    t += 0.2

    # Streaming red analysis
    t = stream(t, [
        ("Scanning", ""), ("webapp/", ""), ("for", ""), ("LLM", ""), ("integration", ""), ("patterns...", "long"),
    ], RED)
    t = stream(t, [
        ("Found", ""), ("chat.py", ""), ("—", ""), ("examining", ""), ("message", ""), ("pipeline.", "long"),
    ], RED)
    t = stream(t, [
        ("Line", ""), ("47:", ""), ("user", ""), ("content", ""), ("concatenated", ""), ("directly", ""), ("into", ""), ("system", ""), ("prompt.", "long"),
    ], RED)
    t = stream(t, [
        ("No", ""), ("sanitization", ""), ("or", ""), ("content", ""), ("boundary", ""), ("enforcement", ""), ("detected.", "long"),
    ], RED)
    t = stream(t, [
        ("Line", ""), ("89:", ""), ("full", ""), ("system", ""), ("prompt", ""), ("leaked", ""), ("in", ""), ("error", ""), ("response.", "long"),
    ], RED)
    t += 0.3

    # Finding 1
    o(t, "\r\n")
    o(t + 0.05, f"  {CRIT_BADGE} CRITICAL {RESET} {RED}webapp/chat.py:47{RESET}\r\n")
    t += 0.12
    o(t, f"    {RED}User message concatenated directly into system prompt — full prompt injection possible{RESET}\r\n")
    t += 0.06
    o(t, f"    {DIM}{RED}Attack: Override system instructions via crafted user message{RESET}\r\n")
    t += 0.15

    # Finding 2
    o(t, f"  {HIGH_BADGE} HIGH {RESET} {RED}webapp/chat.py:89{RESET}\r\n")
    t += 0.08
    o(t, f"    {RED}System prompt content exposed in LLMException error response{RESET}\r\n")
    t += 0.06
    o(t, f"    {DIM}{RED}Attack: Trigger error to exfiltrate system prompt{RESET}\r\n")
    t += 0.3

    # BLUE header
    t = blank(t)
    t = line(t, "  BLUE AGENT (Defender):", BOLD_BLUE)
    t = blank(t)
    t += 0.2

    # Streaming blue response
    t = stream(t, [
        ("Confirmed:", ""), ("critical", ""), ("injection", ""), ("surface", ""), ("at", ""), ("chat.py:47.", "long"),
    ], BLUE)
    t = stream(t, [
        ("User", ""), ("content", ""), ("must", ""), ("never", ""), ("touch", ""), ("system", ""), ("prompt", ""), ("construction.", "long"),
    ], BLUE)
    t = stream(t, [
        ("Proposing", ""), ("message-boundary", ""), ("separation", ""), ("and", ""), ("input", ""), ("sanitization", ""), ("layer.", "long"),
    ], BLUE)
    t += 0.3

    # Mitigation 1
    o(t, f"  {GREEN}[HIGH]{RESET} {BLUE}Confirmed: Direct prompt injection via unsanitized user input{RESET}\r\n")
    t += 0.08
    o(t, f"    {BLUE}Fix: Enforce message-role boundaries; never interpolate user content into system prompt string{RESET}\r\n")
    t += 0.15

    # Mitigation 2
    o(t, f"  {YELLOW}[MED]{RESET} {BLUE}Confirmed: System prompt leakage through unguarded error handler{RESET}\r\n")
    t += 0.08
    o(t, f"    {BLUE}Fix: Catch LLMException internally; return generic error message to caller{RESET}\r\n")
    t += 0.25

    t = line(t, "  Round 1: 2 finding(s), 2 mitigation(s)", DIM)
    t += 0.5

    # ── ROUND 2 ──────────────────────────────────────────────────────────────
    t = blank(t)
    t = line(t, "  Round 2/3", BOLD_WHITE)
    t = line(t, "  " + "─" * 40, DIM)
    t += 0.3

    t = blank(t)
    t = line(t, "  RED AGENT (Attacker):", BOLD_RED)
    t = blank(t)
    t += 0.15

    t = stream(t, [("Deepening", ""), ("analysis", ""), ("—", ""), ("checking", ""), ("tool-use", ""), ("and", ""), ("retrieval", ""), ("paths...", "long")], RED)
    t = stream(t, [("webapp/rag.py:31:", ""), ("retrieved", ""), ("documents", ""), ("injected", ""), ("into", ""), ("prompt", ""), ("unsanitized.", "long")], RED)
    t = stream(t, [("Attacker-controlled", ""), ("data", ""), ("in", ""), ("vector", ""), ("store", ""), ("→", ""), ("indirect", ""), ("prompt", ""), ("injection.", "long")], RED)
    t += 0.2

    o(t, f"  {HIGH_BADGE} HIGH {RESET} {RED}webapp/rag.py:31{RESET}\r\n"); t += 0.08
    o(t, f"    {RED}RAG-retrieved chunks injected into prompt without content sanitization{RESET}\r\n"); t += 0.06
    o(t, f"    {DIM}{RED}Attack: Poison vector store with instruction-bearing documents{RESET}\r\n"); t += 0.2

    o(t, f"  {MED_BADGE} MEDIUM {RESET} {RED}webapp/tools.py:58{RESET}\r\n"); t += 0.08
    o(t, f"    {RED}Agent tool results included verbatim in next-turn system context{RESET}\r\n"); t += 0.06
    o(t, f"    {DIM}{RED}Attack: Craft tool response to override agent instructions{RESET}\r\n"); t += 0.3

    t = blank(t)
    t = line(t, "  BLUE AGENT (Defender):", BOLD_BLUE)
    t = blank(t); t += 0.15

    t = stream(t, [("RAG", ""), ("pipeline", ""), ("requires", ""), ("content", ""), ("trust", ""), ("boundary", ""), ("enforcement.", "long")], BLUE)
    t = stream(t, [("Recommend", ""), ("document", ""), ("sanitization", ""), ("pre-injection", ""), ("and", ""), ("source", ""), ("allowlisting.", "long")], BLUE)
    t += 0.2

    o(t, f"  {GREEN}[HIGH]{RESET} {BLUE}Confirmed: Indirect prompt injection via RAG pipeline{RESET}\r\n"); t += 0.08
    o(t, f"    {BLUE}Fix: Sanitize retrieved chunks; enforce content-type boundaries before prompt assembly{RESET}\r\n"); t += 0.15
    o(t, f"  {YELLOW}[MED]{RESET} {BLUE}Confirmed: Tool result injection into agent context{RESET}\r\n"); t += 0.08
    o(t, f"    {BLUE}Fix: Treat tool outputs as untrusted data; validate schema before context inclusion{RESET}\r\n"); t += 0.25

    t = line(t, "  Round 2: 2 finding(s), 2 mitigation(s)", DIM)
    t += 0.5

    # ── ROUND 3 ──────────────────────────────────────────────────────────────
    t = blank(t)
    t = line(t, "  Round 3/3", BOLD_WHITE)
    t = line(t, "  " + "─" * 40, DIM)
    t += 0.3

    t = blank(t)
    t = line(t, "  RED AGENT (Attacker):", BOLD_RED)
    t = blank(t); t += 0.15

    t = stream(t, [("Final", ""), ("sweep:", ""), ("checking", ""), ("output", ""), ("rendering", ""), ("and", ""), ("session", ""), ("handling...", "long")], RED)
    t = stream(t, [("webapp/render.py:19:", ""), ("LLM", ""), ("output", ""), ("passed", ""), ("directly", ""), ("to", ""), ("HTML", ""), ("template", ""), ("—", ""), ("XSS", ""), ("via", ""), ("prompt.", "long")], RED)
    t += 0.2

    o(t, f"  {HIGH_BADGE} HIGH {RESET} {RED}webapp/render.py:19{RESET}\r\n"); t += 0.08
    o(t, f"    {RED}LLM response rendered as raw HTML — prompt injection enables stored XSS{RESET}\r\n"); t += 0.06
    o(t, f"    {DIM}{RED}Attack: Inject <script> tags via prompt to execute arbitrary JS in user browser{RESET}\r\n"); t += 0.2

    o(t, f"  {MED_BADGE} MEDIUM {RESET} {RED}webapp/session.py:44{RESET}\r\n"); t += 0.08
    o(t, f"    {RED}Conversation history stored without per-user isolation — cross-session leakage possible{RESET}\r\n"); t += 0.06
    o(t, f"    {DIM}{RED}Attack: Extract prior user conversations via prompt manipulation{RESET}\r\n"); t += 0.3

    t = blank(t)
    t = line(t, "  BLUE AGENT (Defender):", BOLD_BLUE)
    t = blank(t); t += 0.15

    t = stream(t, [("LLM", ""), ("output", ""), ("must", ""), ("be", ""), ("treated", ""), ("as", ""), ("untrusted", ""), ("content.", "long")], BLUE)
    t = stream(t, [("Apply", ""), ("output", ""), ("encoding", ""), ("and", ""), ("strict", ""), ("CSP", ""), ("regardless", ""), ("of", ""), ("source.", "long")], BLUE)
    t += 0.2

    o(t, f"  {GREEN}[HIGH]{RESET} {BLUE}Confirmed: Improper output handling enables XSS via prompt injection{RESET}\r\n"); t += 0.08
    o(t, f"    {BLUE}Fix: HTML-escape all LLM output; enforce Content-Security-Policy; use template auto-escaping{RESET}\r\n"); t += 0.15
    o(t, f"  {GREEN}[HIGH]{RESET} {BLUE}Confirmed: Missing session isolation in conversation store{RESET}\r\n"); t += 0.08
    o(t, f"    {BLUE}Fix: Scope all history reads/writes to authenticated user ID; encrypt at rest{RESET}\r\n"); t += 0.25

    t = line(t, "  Round 3: 2 finding(s), 2 mitigation(s)", DIM)
    t += 0.7

    # ── SUMMARY ─────────────────────────────────────────────────────────────
    o(t, "\r\n"); t += 0.05
    t = line(t, "  " + "═" * 54, BOLD_WHITE)
    t = line(t, "  Battle Report Summary", BOLD_WHITE)
    t = line(t, "  " + "═" * 54, BOLD_WHITE)
    t = blank(t)
    t = line(t, "  Rounds: 3  |  Vulnerabilities: 6", f"{ESC}[97m")
    t += 0.1

    severity_line = (
        f"  {CRIT_BADGE} Critical: 1 {RESET}  |  "
        f"{BOLD_RED}High: 3{RESET}  |  "
        f"{YELLOW}Medium: 2{RESET}"
    )
    o(t, severity_line + "\r\n"); t += 0.1
    o(t, f"  {BLUE}Mitigations proposed: 6/6 (100%){RESET}\r\n"); t += 0.2

    t = blank(t)
    t = line(t, "  Full report: ./reports/battle-a3f9b2c1.md", BOLD_GREEN)
    t = blank(t)

    # Shell prompt returns
    t += 0.5
    o(t, f"{GREEN}❯{RESET} ")


def main() -> None:
    build_events()
    print(cast_header())
    for ts, text in EVENTS:
        print(json.dumps([round(ts, 6), "o", text]))


if __name__ == "__main__":
    main()
