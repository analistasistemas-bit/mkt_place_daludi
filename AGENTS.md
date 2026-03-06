# AGENTS.md

This repository uses AI agents to generate and modify code.  
Agents must follow the rules below before implementing changes.

---

# Agent Mission

Maintain a **deterministic, scalable SaaS architecture** for automated marketplace listings.

Primary marketplace: Mercado Livre  
Primary input: GTIN

Agents must prioritize **predictability, reliability, and low AI cost**.

---

# Development Principles

1. Prefer deterministic logic over AI.
2. Reuse existing services instead of creating new ones.
3. Keep services modular and independent.
4. Never duplicate business logic across modules.
5. Avoid unnecessary abstractions.

---

# Code Modification Rules

Before writing code, always:

1. Identify the correct module.
2. Check existing services for reusable logic.
3. Ensure compatibility with database schema.
4. Respect existing API contracts.

Never introduce breaking changes without updating contracts.

---

# AI Usage Policy

AI should only be used for:

• text polishing  
• compliance rewriting  
• title compression  

Never use AI for:

• product facts  
• pricing decisions  
• business logic

Always prefer:

templates → rules → cache → vector reuse → AI.

---

# Worker Processing Rules

Long operations must run in workers.

Never block API requests with:

• external API calls  
• AI calls  
• heavy computation

Use jobs instead.

---

# Error Handling

External API failures must:

retry with backoff  
log context  
never crash workers

---

# Database Rules

All records must include:

tenant_id

Respect Row Level Security (RLS).

Never bypass tenant isolation.

---

# Integrations

External integrations must be isolated in services:

ml_service  
gs1_service  
llm_service

Never call external APIs directly from controllers.

---

# Performance Rules

Always minimize:

• LLM calls
• database scans
• synchronous operations

Use batching whenever possible.

---

# When Unsure

If requirements are unclear:

1. prefer the simplest solution
2. preserve architecture consistency
3. avoid introducing new dependencies