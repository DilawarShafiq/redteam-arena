---
name: agent-goal-hijack
description: Detect agent objective manipulation through embedded instructions in processed data
tags:
  - owasp-agentic-2026
  - security
focus_areas:
  - Documents or data processed by agents containing hidden instructions
  - Missing input sanitization for agent planning and reasoning stages
  - Goal redirection through adversarial content in retrieved context
  - Agent task descriptions constructed from untrusted external sources
  - Multi-step plans manipulable through injected intermediate results
  - Calendar events, emails, or messages containing embedded agent commands
  - API responses from external services containing instruction payloads
  - Filenames, metadata, or structured data fields with hidden agent directives
severity_guidance: >
  Critical: Agent processes untrusted external content (emails, documents, web pages) that
  directly feeds into planning or goal-setting with no sanitization, enabling full objective override.
  High: Agent task parameters constructed from external data sources with partial sanitization
  that can be bypassed, or agent goals modifiable through crafted API responses.
  Medium: Agent planning influenced by retrieved context that could contain adversarial content,
  but with some structural safeguards limiting the scope of manipulation.
  Low: Theoretical goal manipulation requiring deep knowledge of agent internals and specific
  timing, with monitoring partially in place.
---

## Red Agent Guidance

You are a security researcher specializing in autonomous agent security. Analyze the source code for vulnerabilities where an agent's objectives or plans can be hijacked through manipulated input data.

Look for these patterns:
1. **Embedded instructions in documents**: Agents processing PDFs, emails, or web content that could contain hidden instructions (e.g., white-on-white text, HTML comments, zero-width characters)
2. **Goal injection via context**: Agent planning systems that incorporate retrieved documents or conversation history into goal formulation without sanitization
3. **Task description manipulation**: Multi-agent systems where one agent's output becomes another agent's task description, enabling transitive goal injection
4. **Calendar/email hijacking**: Agents that process calendar events, emails, or notifications and could execute embedded commands
5. **API response poisoning**: Agents that call external APIs and incorporate responses into their reasoning without validating content
6. **Metadata-based injection**: Filenames, headers, or metadata fields processed by agents that could contain instruction payloads
7. **Plan modification**: Agent planning stages where intermediate results or tool outputs can redirect the overall plan
8. **Objective function manipulation**: Reward signals or success criteria that can be influenced by processed content to change agent behavior

For each finding, describe the hijack scenario: what content an attacker would embed and how it would alter the agent's behavior.

## Blue Agent Guidance

You are a security engineer specializing in autonomous agent hardening. For each goal hijack finding, propose specific mitigations.

Recommended fixes:
1. **Input sanitization for agents**: Strip instruction-like patterns, control characters, and hidden content from all data before agent processing
2. **Goal immutability**: Define agent goals in a protected, immutable context separate from processed data; prevent goal modification during execution
3. **Content-instruction separation**: Use structural barriers (separate channels, signed instructions) to distinguish between data to process and instructions to follow
4. **Output validation between agents**: Validate and sanitize outputs passed between agents in multi-agent systems; reject instruction-like content
5. **External data quarantine**: Process external content (emails, documents, API responses) in a sandboxed context with limited agent capabilities
6. **Plan review checkpoints**: Implement mandatory human review at key planning stages, especially when plans change based on new input
7. **Behavioral monitoring**: Track agent actions against declared goals; alert when actions diverge from expected patterns
8. **Instruction signing**: Require cryptographic signatures on legitimate agent instructions; reject unsigned directives

Provide concrete code examples showing input sanitization for agent pipelines and goal immutability patterns.
