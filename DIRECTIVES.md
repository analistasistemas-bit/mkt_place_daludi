# DIRECTIVES.md

Global engineering directives for this repository.

These rules are mandatory for all AI agents and developers.

---

# 1. Architecture Integrity

Do not change the system architecture without explicit instruction.

Maintain the separation between:

API  
Workers  
Services  
Database  
Frontend

Business logic must remain inside services.

---

# 2. Deterministic First

Always prefer deterministic logic.

Order of execution:

rules → templates → cache → vector reuse → AI

AI must be the final fallback.

---

# 3. Service Isolation

External integrations must be isolated in services.

Allowed integration points:

ml_service  
gs1_service  
llm_service

Controllers and workers must never call external APIs directly.

---

# 4. Worker Responsibility

Long or external operations must run in workers.

Never perform in API layer:

external API calls  
LLM calls  
heavy computations

---

# 5. Multi-Tenant Safety

All database operations must include:

tenant_id

Never bypass Row Level Security.

Tenant isolation is mandatory.

---

# 6. API Contract Stability

Existing API contracts must not break.

If modification is required:

update schema  
update documentation  
maintain backward compatibility

---

# 7. Data Integrity

Never fabricate product information.

Product attributes must originate from:

GS1  
verified product sources  
trusted marketplace data

---

# 8. Performance Protection

Avoid:

large synchronous operations  
unbounded database queries  
unnecessary LLM usage

Prefer:

batch processing  
indexed queries  
cached responses

---

# 9. Observability

All critical operations must log:

tenant_id  
job_id  
service

Errors must include context.

---

# 10. Dependency Discipline

Do not introduce new dependencies unless strictly necessary.

Prefer existing libraries and utilities.

---

# 11. Security

Never expose:

API keys  
service credentials  
database secrets

Frontend must never access external services directly.