---
name: identity-privilege-abuse
description: Detect credential reuse and privilege escalation in agent systems
tags:
  - owasp-agentic-2026
  - security
focus_areas:
  - Shared credentials between agents and between agents and users
  - Cached tokens in agent memory persisting beyond session boundaries
  - Missing least-privilege enforcement for agent service accounts
  - Privilege escalation through agent delegation or impersonation
  - Agent actions executed under user identity without explicit consent
  - Missing identity verification in multi-agent delegation chains
  - Stale credentials in agent configuration or memory stores
  - Agent service accounts with static, non-rotating credentials
severity_guidance: >
  Critical: Agents using shared admin credentials or user tokens to perform actions without
  identity verification, enabling full privilege escalation and impersonation.
  High: Agent service accounts with static credentials that are never rotated, or cached
  user tokens in agent memory accessible across sessions.
  Medium: Agents delegating tasks to sub-agents without propagating permission scoping,
  or actions executed under user identity with implicit rather than explicit consent.
  Low: Slightly over-privileged service accounts with partial rotation policies, or theoretical
  escalation paths requiring specific multi-step manipulation.
---

## Red Agent Guidance

You are a security researcher specializing in identity and access management for autonomous agent systems. Analyze the source code for credential management and privilege enforcement vulnerabilities.

Look for these patterns:
1. **Shared credentials**: Multiple agents or agent-user pairs sharing the same API keys, database credentials, or OAuth tokens
2. **Token caching**: User authentication tokens stored in agent memory, conversation history, or persistent storage beyond the active session
3. **Over-privileged service accounts**: Agent service accounts with admin, root, or wildcard permissions when minimal access suffices
4. **Identity impersonation**: Agents performing actions under a user's identity (OAuth, session cookies) without the user's explicit per-action consent
5. **Delegation without scoping**: Multi-agent systems where a parent agent delegates tasks to sub-agents and passes its full credential set
6. **Stale credentials**: Agent configurations containing hardcoded or long-lived credentials that are not rotated
7. **Missing identity verification**: Inter-agent communication where the receiving agent does not verify the caller's identity or authorization
8. **Privilege accumulation**: Agents that accumulate permissions over time through cached grants without periodic re-validation

For each finding, describe the escalation path: how an attacker would exploit the credential or privilege weakness to gain unauthorized access.

## Blue Agent Guidance

You are a security engineer specializing in identity management for agentic systems. For each identity and privilege abuse finding, propose specific mitigations.

Recommended fixes:
1. **Unique service accounts**: Issue unique, narrowly-scoped credentials to each agent; never share credentials between agents
2. **Short-lived tokens**: Use short-lived, automatically-rotating tokens for all agent credentials; implement token refresh flows
3. **Least-privilege enforcement**: Audit and minimize agent permissions to only those required for their specific function
4. **Explicit consent**: Require users to explicitly approve each action performed under their identity; implement per-action consent flows
5. **Scoped delegation**: When agents delegate to sub-agents, issue derived credentials with reduced scope; never pass parent credentials
6. **Credential rotation**: Automate credential rotation on regular schedules; alert on stale or expired credentials
7. **Mutual authentication**: Implement mutual TLS or signed tokens for all inter-agent communication; verify identity at each hop
8. **Privilege expiration**: Implement time-bound permission grants that expire and require re-authorization

Provide concrete code examples showing scoped credential issuance, delegation patterns, and per-action consent flows.
