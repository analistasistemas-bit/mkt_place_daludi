# Fase 2 — API Core — Plano de Implementação

> **Para Claude:** SUB-SKILL OBRIGATÓRIA: Use superpowers:executing-plans para implementar este plano tarefa a tarefa.

**Objetivo:** Criar toda a camada de API FastAPI com autenticação Supabase, middleware multi-tenant, rate limit, e todos os endpoints MVP.

**Arquitetura:** FastAPI com dependências injetadas via `Depends()`, middleware de auth via JWT Supabase, isolamento por tenant_id, e rate limit por tenant/IP.

**Tech Stack:** FastAPI, Supabase Python SDK, python-jose (JWT), uvicorn

---

## Task 1: Supabase Client + Dependências

**Arquivos:** Criar `apps/api/deps.py`

Implementar:
- `get_supabase_client()` — client admin (service_role_key)
- `get_supabase_anon_client()` — client anon
- `get_current_user()` — dependência que valida JWT e retorna user
- `get_tenant_id()` — extrai tenant_id do user autenticado

---

## Task 2: Middleware Auth (JWT Supabase)

**Arquivos:** Criar `apps/api/middleware/auth.py`

Implementar:
- Validação de JWT do Supabase Auth
- Extração de user_id e tenant_id do token
- Rejeição de requests sem token válido
- Exceção para rotas públicas (health, docs)

---

## Task 3: Middleware Tenant + Rate Limit

**Arquivos:**
- Criar `apps/api/middleware/tenant.py`
- Criar `apps/api/middleware/rate_limit.py`

Tenant: injetar tenant_id no request state para uso nos routers
Rate Limit: limite básico por IP (em memória, sem Redis por enquanto)

---

## Task 4: Routers — Auth + Products

**Arquivos:**
- Criar `apps/api/routers/auth.py`
- Criar `apps/api/routers/products.py`

Auth: `POST /auth/login` (proxy para Supabase Auth)
Products: `POST /products/import`, `GET /products`, `GET /products/{id}`

---

## Task 5: Routers — Jobs + Listings + Discovery

**Arquivos:**
- Criar `apps/api/routers/jobs.py`
- Criar `apps/api/routers/listings.py`
- Criar `apps/api/routers/discovery.py`

Jobs: `GET /jobs/{id}`
Listings: `GET /listings`, `POST /listings/{id}/publish`
Discovery: `GET /discovery/opportunities` (stub)

---

## Task 6: Main App FastAPI

**Arquivos:** Criar `apps/api/main.py`

Implementar:
- FastAPI app com metadata
- Include de todos os routers
- Middleware CORS, Auth, Tenant
- Health check endpoint
- Startup/shutdown events

---

## Task 7: Dockerfile + Verificação

**Arquivos:** Criar `apps/api/Dockerfile`

Verificação:
- Instalar dependências e importar todos os módulos
- Subir API com uvicorn e testar health check
