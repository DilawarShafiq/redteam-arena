---
name: full-audit
description: Run all scenarios sequentially (sql-injection, xss, auth-bypass, secrets-exposure)
is_meta: true
sub_scenarios:
  - sql-injection
  - xss
  - auth-bypass
  - secrets-exposure
focus_areas:
  - All vulnerability categories
severity_guidance: >
  Uses severity guidance from each individual scenario.
---

## Red Agent Guidance

This is a meta-scenario that runs all attack categories sequentially. Each sub-scenario provides its own specialized Red agent guidance.

## Blue Agent Guidance

This is a meta-scenario that runs all defense categories sequentially. Each sub-scenario provides its own specialized Blue agent guidance.
