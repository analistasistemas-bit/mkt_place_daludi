

## PROMPT MONOREPO DEFINITIVO — “gerar tudo pronto para deploy”

Aja como um **Tech Lead / Staff Engineer** especialista em **monorepos**, **FastAPI**, **workers com fila**, **Supabase (Postgres + RLS + Storage)**, **Next.js (Vercel)**, integração com **Mercado Livre**, integrações de catálogo via **GTIN (GS1/CNP/Verified by GS1)**, e otimização extrema de custo de IA (templates + gates + batching + cache + vector similarity).
Você vai **criar um monorepo completo** com código funcional, documentação e scripts de deploy.

OBJETIVO
Gerar um monorepo com:

1. Banco (Supabase): schema SQL + RLS + pgvector + seeds básicos
2. Backend API (FastAPI): autenticação, multi-tenant, endpoints MVP, enqueue de jobs
3. Worker (Python): orquestra jobs com fila (Redis), retries/backoff/DLQ, rate limit por integração
4. Services: Mercado Livre, GS1/Verified, normalização, identity resolver, pricing, templates, compliance, LLM layer (batch/cached), vector similarity (pgvector)
5. Frontend (Next.js): login, upload planilha, dashboard produtos, jobs, revisão humana, publicar, discovery (stub)
6. Docs: arquitetura, contratos, OpenAPI, setup local, deploy Vercel/Render/Supabase
7. Tooling: lint/format, tests mínimos, env sample, Makefile/Taskfile, docker compose local (se aplicável)

STACK FIXA

* Frontend: Next.js/React (Vercel)
* API: FastAPI (Render)
* Worker: Python (Render) serviço separado
* DB/Auth/Storage: Supabase
* Queue: Redis + RQ (ou Celery se você julgar melhor; prefira RQ pela simplicidade)
* Vector: pgvector no Postgres (Supabase)
* Linguagem: Python 3.11+
* Monorepo: root com apps/ e packages/

PRINCÍPIOS OBRIGATÓRIOS (IMPORTANTE)

* Sistema híbrido: pipeline determinístico + IA só como camada fina/último recurso.
* IA custo baixo: templates determinísticos → compliance rules → (gating) → LLM batch polish/rewrite apenas se necessário.
* Batching: 10–30 itens por chamada LLM quando possível (agrupado por categoria).
* Cache agressivo: não pagar 2x se nada mudou. Se só mudar preço/estoque → sem LLM.
* Vector similarity copy reuse: armazenar copies aprovadas e reusar estruturas com pgvector.
* Multi-tenant governance: RLS, quotas por tenant, rate limit por tenant e por integração.
* Observabilidade: logs estruturados por job/tenant/integration e métricas básicas.

FUNCIONALIDADE MVP (AGENT 1)
Entrada principal: GTIN (manual ou planilha CSV/XLSX), custo opcional.
Entrada secundária: imagem (opcional; pode ficar como stub no MVP).
Fontes: CNP/GS1/Verified by GS1 (quando houver), Google apenas para enriquecimento controlado, Mercado Livre para concorrência e precificação.
Fluxo: import → resolve produto → normaliza → identidade/confiança → concorrência ML → preço → template → compliance → (gates/LLM) → revisão humana (TESTES) → publicar ML.
Discovery (AGENT 2): deixar como stub com tabela/opportunities + endpoint e UI básica, sem lógica pesada no MVP.

CONTRATOS (crie como “fonte de verdade” em docs/)
Defina JSON schemas e dataclasses/pydantic para:

* ProductResolved (RESOLVED | NEEDS_REVIEW | BLOCKED)
* ListingDraft
* ListingReady
* JobEvent
* DiscoveryOpportunity
  Inclua idempotency keys e versionamento.

ENDPOINTS MVP (API)

* POST /auth/login (ou usar Supabase Auth diretamente no frontend; escolha o mais simples e seguro)
* POST /products/import (planilha ou lista de gtins)
* GET /products
* GET /products/{id}
* GET /jobs/{id}
* GET /listings
* POST /listings/{id}/publish
* GET /discovery/opportunities (stub)
  Requisitos: JWT, tenant middleware, rate limit básico.

JOBS (WORKER)

* product.import
* product.resolve
* listing.generate
* listing.publish
* discovery.scan (stub)
  Implementar: retry, backoff exponencial com jitter, DLQ, idempotência.

INTEGRAÇÕES

* Mercado Livre: criar ml_service com funções:

  * search_similar_listings
  * get_category_attributes (stub se necessário)
  * publish_listing
  * update_price
  * update_stock
* GS1/CNP/Verified: criar gs1_service (deixar adaptável: pode ser placeholder se não houver API pública). O importante é o design:

  * lookup_by_gtin
  * validate_gtin_owner
* Google enrichment: criar enrichment_service com regras de “nunca colar textão” (extrair só campos curtos).
* LLM: criar llm_service com:

  * batch_polish_listings
  * rewrite_compliance_spans
  * compress_title
  * JSON strict + validator + fallback premium
* Vector: vector_service com:

  * embed_text
  * find_similar_copies
  * save_approved_copy
    Obs: se não houver provedor de embeddings no MVP, implemente interface + stub e deixe pronto para plugar depois.

COMPLIANCE

* compliance_rules.py (determinístico): regras/regex + lista de termos arriscados + marcação de spans.
* LLM só reescreve spans marcados quando necessário.

TEMPLATES

* template_renderer.py com templates por categoria (mínimo 3 categorias genéricas: “eletrônicos”, “casa”, “beleza”), versionados.
* listing_builder.py monta ListingDraft determinístico.

BANCO (SUPABASE)
Criar SQL completo com:

* tenants, users (ou mapear users do Supabase Auth + tabela profile), products, product_sources, product_evidence, listings, listing_versions, jobs, job_events, copy_templates, vector_embeddings, llm_cache, audit_logs, caches.
* índices essenciais
* pgvector extension
* RLS por tenant_id (policies em arquivo separado)
* seeds mínimos: 1 tenant, 1 template por categoria, 1 usuário de teste (se viável)

MONOREPO E ESTRUTURA (OBRIGATÓRIA)
Crie esta estrutura:

/ (root)
/apps
/api            (FastAPI)
/worker         (Worker RQ/Celery)
/web            (Next.js)
/packages
/shared         (schemas Pydantic, utils, logging, config)
/docs
architecture.md
contracts.md
api-openapi.md (ou openapi.yaml)
setup-local.md
deploy.md
/supabase
schema.sql
rls.sql
seeds.sql
docker-compose.yml (local dev: api + worker + redis; supabase externo)
.env.example (root + por app)
Makefile (ou taskfile) com comandos: dev, lint, test, migrate, seed
README.md

PADRÕES DE CÓDIGO

* Python: ruff + black + mypy (mínimo)
* JS/TS: eslint + prettier
* Use pydantic settings para config via env
* Logging estruturado JSON

DEPLOY (OBRIGATÓRIO)
Crie instruções claras e arquivos de configuração para:

* Vercel: deploy do /apps/web
* Render:

  * service API: start uvicorn
  * service Worker: start worker
* Supabase: aplicar schema + RLS + seeds
* Redis: instruir como configurar (Render Redis ou Upstash) e variáveis.

ENTREGA (O QUE VOCÊ DEVE PRODUZIR AGORA)

1. Liste todos os arquivos que você vai criar/editar (com caminho).
2. Em seguida, escreva o conteúdo completo de cada arquivo principal (pelo menos):

   * apps/api/main.py + routers + auth/middleware + supabase client
   * apps/worker/worker.py + job handlers
   * packages/shared/schemas.py (pydantic)
   * services: ml_service.py, gs1_service.py, normalizer.py, identity_resolver.py, pricing.py, template_renderer.py, compliance_rules.py, llm_service.py, vector_service.py
   * supabase/schema.sql + rls.sql + seeds.sql
   * apps/web páginas principais + service client
   * docs/setup-local.md + docs/deploy.md + docs/contracts.md
   * docker-compose.yml + .env.example + Makefile
3. Garanta que o projeto roda localmente com:

   * `make dev` (ou comando equivalente)
4. Inclua “mocks/stubs” para integrações que dependem de credenciais, mas mantenha interfaces prontas.
5. Não invente credenciais. Use variáveis de ambiente e placeholders.

COMECE AGORA: crie o monorepo completo.

---

### Observação importante (pra você executar sem dor)

Depois que o vibecoding gerar o monorepo, sua ordem prática vira:

1. Subir Supabase (schema + RLS + seeds)
2. Rodar local com Redis + API + Worker
3. Conectar Mercado Livre (credenciais)
4. Ligar LLM barata (credenciais)
5. Publicar MVP (Vercel + Render)


