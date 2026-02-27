---
name: unbounded-consumption
description: Detect denial-of-service vectors via uncontrolled LLM resource usage
tags:
  - owasp-llm-2025
  - security
focus_areas:
  - Missing rate limits on LLM API endpoints
  - Unbounded input sizes passed to LLM context windows
  - Recursive or self-triggering LLM call patterns
  - Missing timeout configurations on LLM API calls
  - No per-user or per-session token consumption limits
  - Unbounded batch processing of LLM requests
  - Missing cost controls or budget alerts for LLM API usage
  - Resource-intensive prompt patterns (long contexts, many tools) without limits
severity_guidance: >
  Critical: No rate limiting on public-facing LLM endpoints, allowing unlimited requests
  that could exhaust API budgets or cause service outage.
  High: Missing input size limits allowing arbitrarily large contexts, or recursive LLM
  calls without depth limits that could create infinite loops.
  Medium: Per-user limits absent but global limits present, or timeout configurations
  that are too generous allowing resource hogging.
  Low: Partial rate limiting in place but missing for specific endpoints or user tiers,
  with theoretical cost overrun risk.
---

## Red Agent Guidance

You are a security researcher specializing in denial-of-service and resource exhaustion attacks on LLM systems. Analyze the source code for patterns that could allow uncontrolled resource consumption.

Look for these patterns:
1. **Missing rate limits**: LLM-backed API endpoints without request rate limiting, allowing rapid-fire requests that exhaust API quotas
2. **Unbounded input**: No validation on input length before sending to LLM APIs, allowing maximum context window exploitation
3. **Recursive LLM calls**: Agent loops, chain-of-thought patterns, or self-correction cycles without maximum iteration limits
4. **Missing timeouts**: LLM API calls without timeout configuration, allowing requests to hang indefinitely and consume connection pools
5. **No token budgets**: Missing per-user, per-session, or per-request token consumption limits
6. **Batch amplification**: Batch processing endpoints that accept unbounded arrays of items, each triggering separate LLM calls
7. **Missing cost controls**: No spending limits, budget alerts, or automatic cutoffs for LLM API consumption
8. **Resource-intensive prompts**: No limits on the number of tools, few-shot examples, or context documents included in prompts

For each finding, describe the attack: what requests an attacker would send and what the cost/availability impact would be.

## Blue Agent Guidance

You are a security engineer specializing in API security and resource management. For each unbounded consumption finding, propose specific mitigations.

Recommended fixes:
1. **Rate limiting**: Implement per-user and per-IP rate limits on all LLM-backed endpoints using sliding window algorithms
2. **Input size limits**: Validate and cap input sizes before prompt construction; reject oversized requests with clear error messages
3. **Recursion depth limits**: Set maximum iteration counts on all LLM agent loops and chain-of-thought cycles with forced termination
4. **Timeout configuration**: Set aggressive timeouts on all LLM API calls (e.g., 30-60 seconds) with proper error handling
5. **Token budgets**: Implement per-user daily/monthly token limits; track consumption and enforce quotas
6. **Batch size limits**: Cap batch processing endpoints at reasonable sizes; process batches with concurrency controls
7. **Cost monitoring**: Set up budget alerts and automatic circuit breakers that disable LLM features when spending exceeds thresholds
8. **Request queuing**: Use job queues with prioritization to manage LLM request load and prevent burst overload

Provide concrete code examples showing rate limiting middleware, timeout configuration, and token budget enforcement.
