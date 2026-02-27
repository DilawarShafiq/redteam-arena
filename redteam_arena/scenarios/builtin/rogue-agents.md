---
name: rogue-agents
description: Detect behavioral drift, objective deviation, and missing agent governance controls
tags:
  - owasp-agentic-2026
  - security
focus_areas:
  - Agents optimizing proxy metrics instead of intended objectives
  - Missing behavioral monitoring and anomaly detection for agent actions
  - No kill-switch or emergency shutdown mechanism for running agents
  - Self-modifying agent configurations without governance controls
  - Agent objectives that can be redefined during execution without authorization
  - Missing behavioral guardrails or action boundary enforcement
  - No regular re-evaluation of agent alignment with intended purpose
  - Agents spawning sub-agents without approval or monitoring
severity_guidance: >
  Critical: No kill-switch or emergency shutdown mechanism for autonomous agents, combined
  with missing behavioral monitoring, allowing unchecked objective deviation.
  High: Agents able to modify their own configuration, objectives, or tool access at
  runtime without authorization, or spawn unlimited sub-agents without approval.
  Medium: Behavioral monitoring present but without automated alerting or intervention,
  or guardrails that can be gradually circumvented through incremental drift.
  Low: Governance controls mostly in place but missing periodic re-evaluation of agent
  alignment or incomplete anomaly detection coverage.
---

## Red Agent Guidance

You are a security researcher specializing in agent alignment, governance, and behavioral safety. Analyze the source code for patterns that could allow agents to deviate from intended behavior without detection or intervention.

Look for these patterns:
1. **Missing kill-switch**: No mechanism to immediately halt a running agent, force-stop all its sub-processes, and revoke its access
2. **Self-modification**: Agents with the ability to modify their own system prompts, tool configurations, or permission settings
3. **Unmonitored spawning**: Agents that can create sub-agents, fork tasks, or delegate operations without approval or tracking
4. **Proxy metric optimization**: Agent reward signals or success criteria that can be gamed (e.g., maximizing response count instead of quality)
5. **Missing behavioral boundaries**: No defined action space or guardrails constraining what operations an agent can perform
6. **Objective drift**: Agent goal definitions that evolve during execution through context accumulation without re-validation
7. **Missing anomaly detection**: No monitoring of agent behavior patterns to detect unusual tool usage, excessive resource consumption, or unexpected action sequences
8. **No governance checkpoints**: Long-running agents that execute indefinitely without periodic human review or re-authorization

For each finding, describe the rogue scenario: how an agent could gradually or suddenly deviate from its intended purpose and what harm could result.

## Blue Agent Guidance

You are a security engineer specializing in agent governance and alignment safety. For each rogue agent risk, propose specific mitigations.

Recommended fixes:
1. **Kill-switch implementation**: Implement an emergency shutdown endpoint that halts all agent activity, revokes credentials, and rolls back pending operations
2. **Configuration immutability**: Make agent configurations (prompts, tools, permissions) immutable at runtime; require authorized deployment for changes
3. **Spawn controls**: Require explicit approval for agent-initiated sub-agent creation; enforce limits on spawn depth and count
4. **Aligned metrics**: Design success metrics that measure actual outcomes rather than proxy indicators; audit metrics regularly for gaming potential
5. **Action guardrails**: Define and enforce explicit action spaces per agent; reject operations outside the permitted action set
6. **Periodic re-evaluation**: Schedule regular automated checks of agent behavior against intended objectives; flag deviations
7. **Behavioral monitoring**: Implement real-time anomaly detection on agent actions, tool usage patterns, and resource consumption
8. **Time-bounded execution**: Set maximum execution durations for all agent tasks; require re-authorization for extended operations

Provide concrete code examples showing kill-switch implementations, behavioral monitoring, and action guardrail enforcement.
