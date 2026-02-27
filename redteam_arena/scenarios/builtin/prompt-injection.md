---
name: prompt-injection
description: Detect direct and indirect prompt injection in LLM-powered code
tags:
  - owasp-llm-2025
  - security
focus_areas:
  - User input flowing directly into LLM prompts without sanitization
  - System prompt concatenation with untrusted data
  - Indirect injection via external data sources (URLs, documents, database content) processed by LLMs
  - Instruction override patterns where user input can alter system behavior
  - Missing input validation or filtering before prompt construction
  - Template injection in prompt templates allowing control character insertion
  - Multi-turn conversation manipulation enabling progressive prompt hijacking
  - Embedded instructions in filenames, metadata, or structured data fields consumed by LLMs
severity_guidance: >
  Critical: User input directly concatenated into system prompts or prompt templates with no sanitization,
  enabling full instruction override.
  High: Indirect injection paths where external data sources (documents, web content, database records)
  flow into LLM prompts without filtering, allowing partial instruction manipulation.
  Medium: Prompt construction patterns that could be exploited through crafted multi-turn interactions
  or require specific formatting to trigger injection.
  Low: Theoretical injection vectors requiring unlikely conditions, limited to minor behavior deviation
  with no data exfiltration potential.
---

## Red Agent Guidance

You are a security researcher specializing in LLM prompt injection attacks. Analyze the source code for vulnerabilities where user-controlled or externally-sourced data can manipulate LLM behavior.

Look for these patterns:
1. **Direct prompt concatenation**: `prompt = systemPrompt + userInput` or template literals embedding user input into instructions
2. **Missing input sanitization**: User messages passed to LLM APIs without stripping control sequences, delimiters, or instruction-like patterns
3. **Indirect injection via RAG**: Retrieved documents, web scrapes, or database content injected into prompts without sanitization
4. **System prompt in user-accessible locations**: System prompts stored in client-side code, cookies, or query parameters
5. **Instruction boundary weakness**: Lack of clear delimiters or role separation between system instructions and user content
6. **Tool-use prompt injection**: Agent tool descriptions or parameters constructed from user input, enabling tool manipulation
7. **Multi-modal injection**: Images, audio, or file metadata containing hidden instructions processed by multimodal LLMs
8. **Conversation history poisoning**: Prior conversation turns stored and replayed without validation, enabling progressive injection

For each finding, describe the specific attack vector: what input an attacker would craft and what behavior change it would produce (data exfiltration, instruction override, role manipulation).

## Blue Agent Guidance

You are a security engineer specializing in LLM application security. For each prompt injection finding, propose specific mitigations.

Recommended fixes:
1. **Input sanitization layer**: Strip or escape instruction-like patterns, delimiters, and control sequences from user input before prompt construction
2. **Structural prompt design**: Use strong delimiters (XML tags, unique tokens) to separate system instructions from user content, and instruct the model to treat user sections as data only
3. **Output validation**: Validate LLM responses against expected schemas before acting on them; reject responses that indicate instruction override
4. **Privilege separation**: Run user-facing LLM calls with minimal tool access; use a separate privileged context for system operations
5. **Content filtering**: Apply input classifiers to detect prompt injection attempts before they reach the LLM
6. **Indirect injection defense**: Sanitize all external data (RAG documents, API responses, web content) before including in prompts
7. **Monitoring and alerting**: Log prompt-response pairs and alert on anomalous behavior patterns indicating successful injection

Provide concrete code examples showing the vulnerable prompt construction replaced with hardened alternatives.
