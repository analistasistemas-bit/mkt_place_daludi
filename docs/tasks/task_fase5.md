# Tarefas — Fases 1 a 5

## Fase 1 — Base (Concluída)
- [x] Estrutura do monorepo
- [x] supabase/schema.sql + rls.sql + seeds.sql
- [x] packages/shared/schemas.py (contratos Pydantic)
- [x] docker-compose.yml + .env.example + Makefile

## Fase 2 — API Core (Concluída)
- [x] apps/api/main.py + auth middleware + tenant middleware
- [x] Routers: products, jobs, listings, discovery (stub)
- [x] Supabase client

## Fase 3 — Services GTIN Pipeline (Concluída)
- [x] normalizer, identity_resolver, pricing
- [x] template_renderer (3 categorias) + listing_builder
- [x] compliance_rules
- [x] ml_service (com stubs para credenciais)
- [x] gs1_service (placeholder adaptável)
- [x] llm_service (batch + cache + stub)
- [x] vector_service (interface + stub embeddings)
- [x] pipeline_orchestrator

## Fase 4 — Worker (Concluída)
- [x] Criar plano de implementação (DLQ, Retry, Idempotência)
- [x] Utilitário base [apps/worker/core.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/core.py) (Decorator Retry+Jitter, DLQ)
- [x] [apps/worker/worker.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/worker.py) (Setup RQ Custom Worker)
- [x] Job handlers (`product.import`, `product.resolve`, `listing.generate`, `listing.publish`, `discovery.scan`)
- [x] Teste simulado de queues/retry

## Fase 5 — Frontend MVP (Planning Concluído)
- [x] Discussão de Brainstorming (shadcn/ui aprovada)
- [x] Visão Lado-a-Lado no /review (Aprovada)
- [x] Documento Design (docs/plans/2026-03-06-frontend-mvp-design.md)
- [x] Plano de Implementação (docs/plans/2026-03-06-frontend-mvp-implementation-plan.md)

### Execução da Fase 5 (A Fazer)
- [x] Task 1: Setup inicial via `create-next-app` e injeção do `shadcn/ui`
- [x] Task 2: Supabase Server-Side Auth e rotas Edge Middleware 
- [x] Task 3: Base Template de Autenticação e Layout
- [x] Task 4: Fluxos de Dados Básicos (Import/Jobs tables)
- [x] Task 5: Componente Hero Lado-a-Lado de `Review e Edição Humana`
