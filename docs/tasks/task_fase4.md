# Tarefas — Fases 1 a 4

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

### Planejamento
- [x] Criar plano de implementação (DLQ, Retry, Idempotência)
- [x] Aprovação do plano

### Task 1 — Infraestrutura
- [x] Utilitário base [apps/worker/core.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/core.py) (Decorator Retry+Jitter, DLQ)
- [x] [apps/worker/worker.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/worker.py) (Setup RQ Custom Worker)

### Task 2 — Job Handlers
- [x] [apps/worker/jobs/import_job.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/jobs/import_job.py) (`product.import`)
- [x] [apps/worker/jobs/resolve_job.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/jobs/resolve_job.py) (`product.resolve`)
- [x] [apps/worker/jobs/generate_job.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/jobs/generate_job.py) (`listing.generate`)
- [x] [apps/worker/jobs/publish_job.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/jobs/publish_job.py) (`listing.publish`)
- [x] [apps/worker/jobs/discovery_job.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/jobs/discovery_job.py) (`discovery.scan` - stub)

### Verificação
- [x] Simular falha de rede para avaliar retry e backoff
- [x] Enfileirar listagem de produto passando por import, resolve, generate e publish.
