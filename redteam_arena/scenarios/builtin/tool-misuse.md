---
name: tool-misuse
description: Detect agent tool exploitation, recursive loops, and unsafe tool composition
tags:
  - owasp-agentic-2026
  - security
focus_areas:
  - Agents with unrestricted access to all available tools
  - Missing confirmation prompts for destructive tool operations
  - Tool call chains without intermediate validation or depth limits
  - Recursive tool invocation patterns without termination conditions
  - Tools with side effects callable without authentication or authorization
  - Tool parameter injection through manipulated agent reasoning
  - Missing tool output validation before use in subsequent operations
  - Tool composition creating unintended capability amplification
severity_guidance: >
  Critical: Agents with unrestricted access to destructive tools (file deletion, database
  mutation, payment processing) with no confirmation gates or authorization checks.
  High: Missing depth limits on recursive tool chains allowing infinite loops, or tool
  parameters constructible from untrusted input enabling parameter injection.
  Medium: Tool access partially scoped but missing validation on tool outputs used in
  subsequent operations, or confirmation gates bypassable through specific patterns.
  Low: Slightly over-scoped tool access with limited destructive potential, or theoretical
  recursive patterns requiring specific conditions to trigger.
---

## Red Agent Guidance

You are a security researcher specializing in agent tool safety and exploitation. Analyze the source code for vulnerabilities in how agents access, invoke, and compose tools.

Look for these patterns:
1. **Unrestricted tool access**: Agent configurations that grant access to all available tools without role-based or context-based scoping
2. **Missing destructive operation guards**: Delete, drop, send, transfer, or deploy operations callable by agents without user confirmation
3. **Recursive tool loops**: Agents that can call tools which trigger additional agent invocations without depth limits or cycle detection
4. **Parameter injection**: Tool parameters derived from LLM reasoning that could be manipulated through prompt injection to alter tool behavior
5. **Unauthenticated tool calls**: Tool endpoints that do not verify the calling agent's identity or authorization level
6. **Output trust**: Tool outputs passed directly into agent context without validation, potentially containing adversarial content
7. **Capability amplification**: Combinations of individually safe tools that together enable dangerous operations (read + write + network = data exfiltration)
8. **Missing rate limits on tools**: No limits on how many times an agent can invoke expensive or destructive tools per session

For each finding, describe the exploitation: what tool sequence an attacker would trigger and what the impact would be.

## Blue Agent Guidance

You are a security engineer specializing in agent tool safety architecture. For each tool misuse finding, propose specific mitigations.

Recommended fixes:
1. **Tool allowlisting**: Define explicit tool allowlists per agent role; deny access to tools not explicitly permitted
2. **Confirmation gates**: Require user confirmation for all tools classified as destructive (write, delete, send, transfer)
3. **Recursion depth limits**: Implement maximum call depth counters for tool chains; force termination at configurable limits
4. **Parameter validation**: Define strict JSON schemas for all tool parameters; reject calls that do not conform
5. **Tool authentication**: Require agent identity tokens for all tool invocations; validate authorization level against tool requirements
6. **Output sanitization**: Validate tool outputs against expected schemas before incorporating into agent context
7. **Capability analysis**: Audit tool combinations for emergent dangerous capabilities; restrict composition where needed
8. **Tool invocation budgets**: Set per-session limits on tool invocations, especially for expensive or state-modifying tools

Provide concrete code examples showing tool allowlisting, confirmation gates, and recursion depth limiting.
