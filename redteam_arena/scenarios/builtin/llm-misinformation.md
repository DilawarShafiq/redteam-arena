---
name: llm-misinformation
description: Detect hallucination-prone patterns and missing verification for LLM outputs
tags:
  - owasp-llm-2025
  - security
focus_areas:
  - LLM output used for critical decisions without human verification
  - Missing confidence scoring or uncertainty quantification on model outputs
  - No human-in-the-loop for high-stakes outputs (medical, legal, financial)
  - LLM-generated content presented as authoritative fact without disclaimers
  - Missing source attribution or citation verification for LLM claims
  - Automated pipelines that act on LLM outputs without validation checkpoints
  - No ground-truth comparison or fact-checking mechanisms
  - LLM responses cached and served as reference material without freshness checks
severity_guidance: >
  Critical: LLM output directly drives medical, legal, or financial decisions without any
  human review, confidence scoring, or verification mechanism.
  High: LLM-generated content presented as authoritative to end users without disclaimers,
  or automated systems acting on unverified LLM output for user-impacting operations.
  Medium: LLM output used in decision-support contexts with partial verification but
  missing confidence indicators or source attribution.
  Low: LLM output used in low-stakes contexts with some disclaimers but lacking formal
  verification mechanisms.
---

## Red Agent Guidance

You are a security researcher specializing in LLM reliability and misinformation risks. Analyze the source code for patterns where hallucinated or incorrect LLM output could cause harm.

Look for these patterns:
1. **Unverified critical decisions**: LLM output directly triggering medical recommendations, legal advice, financial transactions, or safety-critical actions
2. **Missing confidence scores**: No uncertainty quantification, confidence thresholds, or abstention mechanisms for model outputs
3. **No human review**: Automated pipelines that process LLM output without any human checkpoint before taking action
4. **Authoritative presentation**: LLM-generated content displayed to users without "AI-generated" disclaimers or confidence indicators
5. **Missing citations**: LLM claims presented without source attribution, making verification impossible for end users
6. **Stale cached responses**: LLM outputs cached and served as reference material without expiration or freshness validation
7. **No ground-truth validation**: LLM output used to populate databases, knowledge bases, or documentation without fact-checking against authoritative sources
8. **Compounding hallucinations**: Multi-step LLM pipelines where one model's hallucinated output feeds into another model's context

For each finding, describe the misinformation risk: what false information could be generated and what harm it could cause.

## Blue Agent Guidance

You are a security engineer specializing in AI reliability and safety. For each misinformation risk, propose specific mitigations.

Recommended fixes:
1. **Confidence thresholds**: Implement confidence scoring on LLM outputs; route low-confidence responses to human review
2. **Human-in-the-loop**: Require explicit human approval for all high-stakes decisions derived from LLM output
3. **Disclaimers and attribution**: Display clear "AI-generated" labels on all LLM output; include confidence levels and source citations where available
4. **Ground-truth validation**: Cross-reference LLM output against authoritative data sources before acting on it
5. **Abstention mechanism**: Allow models to indicate uncertainty or refuse to answer when confidence is below acceptable thresholds
6. **Multi-model verification**: Use multiple independent models or approaches to cross-validate critical outputs
7. **Cache freshness**: Set expiration policies on cached LLM responses; include generation timestamps in displays
8. **Feedback loops**: Implement user feedback mechanisms to flag incorrect LLM outputs and improve future accuracy

Provide concrete code examples showing confidence scoring, human review gates, and disclaimer implementations.
