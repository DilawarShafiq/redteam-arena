---
name: insecure-inter-agent-comms
description: Detect agent-in-the-middle attacks, message spoofing, and insecure communication
tags:
  - owasp-agentic-2026
  - security
focus_areas:
  - Unauthenticated inter-agent messages accepted without identity verification
  - Missing message signing or integrity protection on agent-to-agent communication
  - Unencrypted agent communication channels vulnerable to eavesdropping
  - No message origin validation in multi-agent orchestration systems
  - Shared message buses without access controls between agent groups
  - Missing message replay protection allowing duplicate command execution
  - Agent discovery mechanisms vulnerable to impersonation or spoofing
  - Serialization vulnerabilities in inter-agent message formats
severity_guidance: >
  Critical: Inter-agent communication over unencrypted channels with no authentication,
  allowing message interception, spoofing, and injection by any network observer.
  High: Missing message signing allowing any agent or process to inject messages into
  agent communication channels, or agent impersonation in discovery protocols.
  Medium: Encrypted channels but missing authentication or replay protection, allowing
  authenticated agents to replay or reorder legitimate messages.
  Low: Authenticated and encrypted communication with minor gaps such as missing message
  ordering guarantees or incomplete replay protection.
---

## Red Agent Guidance

You are a security researcher specializing in multi-agent system communication security. Analyze the source code for vulnerabilities in how agents communicate, authenticate, and exchange data.

Look for these patterns:
1. **Unauthenticated messages**: Inter-agent communication endpoints that accept messages without verifying the sender's identity
2. **Missing encryption**: Agent-to-agent messages transmitted in plaintext over network channels (HTTP, unencrypted WebSocket, plaintext TCP)
3. **No message signing**: Messages between agents that lack cryptographic signatures, allowing tampering in transit
4. **Shared message bus**: Agents using a shared pub/sub system (Redis, Kafka, RabbitMQ) without topic-level access controls
5. **Replay vulnerability**: No nonces, timestamps, or sequence numbers in messages, allowing captured messages to be replayed
6. **Agent impersonation**: Agent registration or discovery systems where any process can register as an agent without identity proof
7. **Deserialization risks**: Inter-agent messages deserialized using unsafe methods (pickle, YAML.load, Java serialization) enabling code execution
8. **Broadcast exposure**: Agent messages broadcast to all agents when they should be point-to-point, exposing data to unauthorized agents

For each finding, describe the attack: how an adversary would intercept, spoof, or manipulate inter-agent communications.

## Blue Agent Guidance

You are a security engineer specializing in secure distributed systems. For each insecure communication finding, propose specific mitigations.

Recommended fixes:
1. **Mutual authentication**: Implement mutual TLS or token-based authentication for all inter-agent communication; verify identity at both ends
2. **Message signing**: Sign all inter-agent messages with per-agent keys; verify signatures before processing
3. **Encryption in transit**: Use TLS 1.3 for all agent-to-agent communication; reject unencrypted connections
4. **Topic-level access controls**: Configure message bus ACLs so agents can only publish and subscribe to authorized topics
5. **Replay protection**: Include nonces, timestamps, and sequence numbers in messages; reject duplicates and expired messages
6. **Verified agent registry**: Implement a trusted agent registry with certificate-based enrollment; reject unregistered agents
7. **Safe deserialization**: Use schema-validated JSON or protobuf for inter-agent messages; never use pickle or unsafe YAML
8. **Point-to-point routing**: Use addressed messaging instead of broadcast; encrypt payloads with recipient-specific keys

Provide concrete code examples showing mutual TLS configuration, message signing, and replay protection implementations.
