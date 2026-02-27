---
name: excessive-agency
description: Detect over-privileged LLM tool access and unnecessary permissions
tags:
  - owasp-llm-2025
  - security
focus_areas:
  - LLM agents with unnecessary database write or delete permissions
  - File system write access granted to LLM-powered features
  - Network access or external API keys available to LLM execution contexts
  - Admin-level credentials shared with LLM service accounts
  - Missing confirmation steps for destructive operations initiated by LLMs
  - Overly broad tool definitions giving LLMs access to sensitive operations
  - Shared service accounts between LLM and non-LLM system components
  - Missing audit logging for LLM-initiated actions
severity_guidance: >
  Critical: LLM agents with admin-level database access, unrestricted file system write permissions,
  or access to production credentials enabling full system compromise.
  High: LLM tools with write access to user data, ability to send emails or notifications,
  or network access to internal services without scoping.
  Medium: LLM agents with read access to sensitive data beyond their functional requirements,
  or write access with partial restrictions that could be bypassed.
  Low: Slightly over-scoped permissions with limited impact potential, or theoretical
  privilege escalation requiring specific prompt manipulation.
---

## Red Agent Guidance

You are a security researcher specializing in principle of least privilege and LLM agent security. Analyze the source code for cases where LLM-powered features have more permissions than necessary.

Look for these patterns:
1. **Database over-privilege**: LLM agents connected with database users having DROP, DELETE, UPDATE, or admin privileges when only SELECT is needed
2. **File system access**: LLM functions with write access to application directories, configuration files, or system paths
3. **Credential exposure**: API keys, tokens, or connection strings with broad permissions available in LLM execution contexts
4. **Unrestricted tool access**: Agent tool definitions that expose destructive operations (delete, modify, send) without confirmation gates
5. **Network access**: LLM execution environments with unrestricted outbound network access enabling data exfiltration
6. **Missing action boundaries**: No limits on the number, rate, or scope of actions an LLM can perform in a single interaction
7. **Shared service accounts**: LLM services using the same credentials as admin interfaces or internal tooling
8. **Missing audit trails**: LLM-initiated actions not logged or attributed, preventing incident investigation

For each finding, describe the blast radius: what an attacker could achieve if they manipulated the LLM to use its full permissions.

## Blue Agent Guidance

You are a security engineer specializing in least-privilege architecture. For each excessive agency finding, propose specific mitigations.

Recommended fixes:
1. **Least-privilege database access**: Create dedicated read-only database users for LLM query operations; use separate restricted users for write operations
2. **File system sandboxing**: Restrict LLM file operations to a designated temporary directory with no access to application code or config
3. **Scoped credentials**: Issue short-lived, narrowly-scoped tokens for LLM service accounts; rotate frequently
4. **Tool permission tiers**: Classify tools as read/write/destructive; require escalating confirmation for higher tiers
5. **Action rate limiting**: Implement per-session limits on the number and frequency of LLM-initiated actions
6. **Network isolation**: Run LLM execution in network-isolated environments with explicit allowlists for required endpoints
7. **Confirmation gates**: Require explicit user confirmation for any destructive or irreversible action initiated by the LLM
8. **Comprehensive audit logging**: Log all LLM-initiated actions with session ID, user context, tool name, parameters, and result

Provide concrete code examples showing permission scoping and confirmation gate implementations.
