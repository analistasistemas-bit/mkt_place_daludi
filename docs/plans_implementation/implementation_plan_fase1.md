# Fase 1 — Base do Monorepo — Plano de Implementação

> **Para Claude:** SUB-SKILL OBRIGATÓRIA: Use superpowers:executing-plans para implementar este plano tarefa a tarefa.

**Objetivo:** Criar toda a fundação do projeto SaaS marketplace (estrutura de diretórios, banco de dados completo no Supabase, contratos Pydantic, e tooling de desenvolvimento).

**Arquitetura:** Monorepo simples com 3 apps (api/worker/web), pacote compartilhado (schemas/config/logging), banco Supabase com RLS multi-tenant, e Redis local para desenvolvimento.

**Tech Stack:** Python 3.11+, FastAPI, Supabase (Postgres 17 + pgvector), Redis, Next.js, Docker Compose, Pydantic v2

---

## Task 1: Estrutura de Diretórios do Monorepo

**Arquivos:**
- Criar: `apps/api/__init__.py`
- Criar: `apps/api/services/.gitkeep`
- Criar: `apps/api/routers/.gitkeep`
- Criar: `apps/api/middleware/.gitkeep`
- Criar: `apps/worker/__init__.py`
- Criar: `apps/worker/jobs/.gitkeep`
- Criar: `apps/web/.gitkeep`
- Criar: `packages/shared/__init__.py`
- Criar: `docs/.gitkeep`
- Criar: `supabase/.gitkeep`

**Passo 1:** Criar todos os diretórios e arquivos placeholder

```bash
cd "/Users/diego/Desktop/IA/mktplace daludi full"
mkdir -p apps/api/services apps/api/routers apps/api/middleware
mkdir -p apps/worker/jobs
mkdir -p apps/web
mkdir -p packages/shared
mkdir -p docs/plans
mkdir -p supabase
touch apps/api/__init__.py apps/api/services/__init__.py apps/api/routers/__init__.py apps/api/middleware/__init__.py
touch apps/worker/__init__.py apps/worker/jobs/__init__.py
touch apps/web/.gitkeep
touch packages/shared/__init__.py
touch docs/.gitkeep
touch supabase/.gitkeep
```

**Passo 2:** Commit

```bash
git init
git add .
git commit -m "chore: scaffold monorepo structure (fase 1)"
```

---

## Task 2: Schema SQL do Banco de Dados

**Arquivos:**
- Criar: `supabase/schema.sql`

**Passo 1:** Criar schema com todas as tabelas conforme CLAUDE.md

Tabelas a criar:
1. `tenants` — organizações/empresas
2. `profiles` — extensão do Supabase Auth users
3. `products` — produtos resolvidos por GTIN
4. `product_sources` — fontes de dados do produto (GS1, ML, Google)
5. `product_evidence` — evidências coletadas
6. `listings` — anúncios gerados
7. `listing_versions` — histórico de versões do anúncio
8. `jobs` — jobs de processamento
9. `job_events` — eventos/logs de cada job
10. `copy_templates` — templates por categoria
11. `vector_embeddings` — copies aprovadas (pgvector)
12. `llm_cache` — cache de chamadas LLM
13. `audit_logs` — log de auditoria
14. `caches` — cache genérico
15. `opportunities` — discovery (stub MVP)

Todas com `tenant_id`, `created_at`, `updated_at`, índices em `gtin`, `tenant_id`, `status`, `created_at`.

**Passo 2:** Commit

```bash
git add supabase/schema.sql
git commit -m "feat: add complete database schema with pgvector"
```

---

## Task 3: Row Level Security (RLS)

**Arquivos:**
- Criar: `supabase/rls.sql`

**Passo 1:** Criar policies RLS por tenant_id para todas as tabelas

Cada tabela terá:
- `SELECT`: WHERE `tenant_id` = `auth.jwt() ->> 'tenant_id'`
- `INSERT`: WITH CHECK `tenant_id` = `auth.jwt() ->> 'tenant_id'`
- `UPDATE`: USING + WITH CHECK por `tenant_id`
- `DELETE`: USING por `tenant_id`

**Passo 2:** Commit

```bash
git add supabase/rls.sql
git commit -m "feat: add RLS policies for multi-tenant isolation"
```

---

## Task 4: Seeds do Banco

**Arquivos:**
- Criar: `supabase/seeds.sql`

**Passo 1:** Criar seeds mínimos:
- 1 tenant de teste
- 3 templates (eletrônicos, casa, beleza)
- Dados mínimos para validação

**Passo 2:** Commit

```bash
git add supabase/seeds.sql
git commit -m "feat: add seed data (tenant + templates)"
```

---

## Task 5: Aplicar Schema no Supabase

**Passo 1:** Aplicar `schema.sql` como migration no Supabase (projeto `cuetfuxvxzlyhienpafc`)

**Passo 2:** Aplicar `rls.sql` como migration

**Passo 3:** Aplicar `seeds.sql` via execute_sql

**Passo 4:** Verificar tabelas criadas

```bash
# Verificação via MCP Supabase:
# list_tables com verbose=true para confirmar todas as 15 tabelas
```

---

## Task 6: Schemas Pydantic (Contratos)

**Arquivos:**
- Criar: `packages/shared/schemas.py`

**Passo 1:** Implementar contratos Pydantic v2:

```python
# Contratos obrigatórios (conforme CLAUDE.md):
# - ProductResolved (status: RESOLVED | NEEDS_REVIEW | BLOCKED)
# - ListingDraft (idempotency_key, tenant_id, version)
# - ListingReady (derived from ListingDraft + compliance OK)
# - JobEvent (job_id, tenant_id, status, timestamps)
# - DiscoveryOpportunity (id, tenant_id, gtin, score) — stub MVP
```

**Passo 2:** Commit

```bash
git add packages/shared/schemas.py
git commit -m "feat: add Pydantic v2 contracts (schemas)"
```

---

## Task 7: Configuração e Logging

**Arquivos:**
- Criar: `packages/shared/config.py`
- Criar: `packages/shared/logging.py`

**Passo 1:** Config com pydantic-settings (todas as env vars do CLAUDE.md)

**Passo 2:** Logging estruturado JSON com tenant_id, job_id, service

**Passo 3:** Commit

```bash
git add packages/shared/config.py packages/shared/logging.py
git commit -m "feat: add config (pydantic-settings) and structured logging"
```

---

## Task 8: Docker Compose + .env.example + Makefile

**Arquivos:**
- Criar: `docker-compose.yml`
- Criar: `.env.example`
- Criar: `Makefile`
- Criar: `README.md`

**Passo 1:** Docker Compose com serviços:
- API (FastAPI com uvicorn)
- Worker (Python RQ)
- Redis

**Passo 2:** `.env.example` com todas as variáveis (sem valores reais)

**Passo 3:** Makefile com comandos: `dev`, `migrate`, `seed`, `lint`, `test`, `deploy-api`, `deploy-worker`, `deploy-web`

**Passo 4:** README.md base com instruções de setup

**Passo 5:** Commit

```bash
git add docker-compose.yml .env.example Makefile README.md
git commit -m "feat: add Docker Compose, env example, Makefile, and README"
```

---

## Plano de Verificação

### Verificação Automatizada
1. **Schema no Supabase**: `list_tables` via MCP → confirmar 15 tabelas criadas
2. **RLS ativo**: verificar via `execute_sql` que RLS está habilitado em todas as tabelas
3. **Schemas Pydantic**: executar import e validação básica

```bash
cd "/Users/diego/Desktop/IA/mktplace daludi full"
python -c "from packages.shared.schemas import ProductResolved, ListingDraft, ListingReady, JobEvent, DiscoveryOpportunity; print('✅ Todos os schemas importados com sucesso')"
```

4. **Docker Compose**: verificar sintaxe

```bash
docker compose config
```

### Verificação Manual
- Acessar o dashboard do Supabase e confirmar visualmente que as tabelas foram criadas
- Verificar no painel do Supabase que RLS está habilitado nas tabelas
