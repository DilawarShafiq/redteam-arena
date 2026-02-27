---
name: cascading-failures
description: Detect error propagation and resilience gaps in multi-agent systems
tags:
  - owasp-agentic-2026
  - security
focus_areas:
  - Missing circuit breakers between agent components and external services
  - Unbounded agent retry loops that amplify failures
  - Cascading tool failures propagating across dependent agent tasks
  - Missing isolation between agent tasks sharing resources
  - No graceful degradation when dependent agents or services fail
  - Error messages from failed agents consumed and acted upon by other agents
  - Missing health checks and liveness probes for agent components
  - Single points of failure in agent orchestration topologies
severity_guidance: >
  Critical: No circuit breakers or isolation between agents, where a single agent failure
  causes cascading collapse across the entire multi-agent system.
  High: Unbounded retry loops in agent-to-agent or agent-to-service calls that amplify
  failures into resource exhaustion. Missing fallback strategies for critical paths.
  Medium: Partial isolation present but error messages from failed components propagated
  into other agents' context without sanitization, potentially causing secondary failures.
  Low: Resilience patterns mostly in place but missing health checks or monitoring for
  early failure detection.
---

## Red Agent Guidance

You are a security researcher specializing in distributed system resilience and failure analysis. Analyze the source code for patterns that could cause cascading failures across multi-agent systems.

Look for these patterns:
1. **Missing circuit breakers**: Agent-to-agent or agent-to-service calls without circuit breaker patterns, allowing repeated calls to failing services
2. **Unbounded retries**: Retry logic without maximum attempt limits, exponential backoff, or jitter, creating retry storms
3. **Cascading tool failures**: Tool errors that propagate through agent chains without error isolation or fallback handling
4. **Shared resource contention**: Multiple agents competing for the same resources (database connections, API rate limits, memory) without coordination
5. **Error message propagation**: Error details from failed agents or tools injected into other agents' prompts, causing reasoning corruption
6. **Missing timeouts**: Agent-to-agent calls or tool invocations without timeout limits, causing indefinite blocking
7. **Single orchestrator failure**: Central orchestrator agents whose failure brings down all sub-agents, with no failover mechanism
8. **Correlated failures**: Multiple agents depending on the same external service with no fallback, creating simultaneous failure across all dependent agents

For each finding, describe the failure cascade: what initial failure would trigger it and how it would propagate through the system.

## Blue Agent Guidance

You are a security engineer specializing in resilient distributed agent architecture. For each cascading failure risk, propose specific mitigations.

Recommended fixes:
1. **Circuit breakers**: Implement circuit breaker patterns (open/half-open/closed) on all inter-agent and agent-to-service calls
2. **Bounded retries**: Configure retries with maximum attempts, exponential backoff, and jitter; fail gracefully after exhaustion
3. **Task isolation**: Run agent tasks in isolated contexts where failures are contained and do not propagate to other tasks
4. **Graceful degradation**: Define fallback behaviors for each agent capability; continue with reduced functionality when dependencies fail
5. **Error sanitization**: Sanitize error messages before propagating to other agents; use structured error codes instead of raw messages
6. **Timeout enforcement**: Set timeouts on all inter-agent calls, tool invocations, and external service requests
7. **Health monitoring**: Implement health check endpoints and liveness probes for all agent components; auto-scale or restart on failure
8. **Redundant orchestration**: Deploy redundant orchestrator agents with leader election or load balancing to eliminate single points of failure

Provide concrete code examples showing circuit breaker implementations, bounded retry patterns, and graceful degradation strategies.
