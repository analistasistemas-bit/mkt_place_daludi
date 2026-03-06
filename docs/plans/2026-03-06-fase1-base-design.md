# Design — Fase 1: Base do Monorepo

## Decisões de Design

| Decisão | Escolha | Motivo |
|---------|---------|--------|
| Redis | Docker local | Sem custo agora, decisão de produção depois |
| pgvector | Habilitar na Fase 1 | Evitar migração futura |
| Monorepo | Simples (sem gerenciador) | Cada app independente, zero overhead |

## Estrutura de Diretórios

```
/
├── apps/
│   ├── api/          # FastAPI (services, routers, middleware)
│   ├── worker/       # Worker RQ (jobs)
│   └── web/          # Next.js (placeholder Fase 5)
├── packages/
│   └── shared/       # schemas.py, config.py, logging.py
├── supabase/
│   ├── schema.sql    # 15 tabelas + pgvector
│   ├── rls.sql       # Policies multi-tenant
│   └── seeds.sql     # Tenant + templates teste
├── docs/
│   └── plans/
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

## Schema do Banco (15 tabelas)

1. **tenants** — organizações multi-tenant
2. **profiles** — extensão do Supabase Auth
3. **products** — produtos resolvidos via GTIN
4. **product_sources** — fontes de dados (GS1, ML, Google)
5. **product_evidence** — evidências coletadas
6. **listings** — anúncios gerados
7. **listing_versions** — versionamento de anúncios
8. **jobs** — jobs de processamento assíncronos
9. **job_events** — log estruturado dos jobs
10. **copy_templates** — templates por categoria (versionados)
11. **vector_embeddings** — copies aprovadas (pgvector)
12. **llm_cache** — cache de chamadas LLM
13. **audit_logs** — auditoria completa
14. **caches** — cache genérico de respostas
15. **opportunities** — discovery (stub MVP)

## Contratos Pydantic

- `ProductResolved` (RESOLVED | NEEDS_REVIEW | BLOCKED)
- `ListingDraft` (idempotency_key, tenant_id, version)
- `ListingReady` (ListingDraft + compliance OK)
- `JobEvent` (job_id, tenant_id, status, timestamps)
- `DiscoveryOpportunity` (stub MVP)
