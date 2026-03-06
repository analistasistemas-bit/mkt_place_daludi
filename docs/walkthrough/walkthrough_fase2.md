# Walkthrough — Fases 1 & 2 Completas ✅

## Fase 1 — Base (Concluída)

- **Monorepo:** `apps/api`, `apps/worker`, `apps/web`, `packages/shared`, `supabase/`, `docs/`
- **Banco (Supabase):** 15 tabelas + pgvector + triggers + RLS multi-tenant + seeds
- **Schemas Pydantic v2:** 5 contratos (ProductResolved, ListingDraft, ListingReady, Job/JobEvent, Discovery)
- **Infra:** docker-compose.yml, .env.example, Makefile, requirements.txt

---

## Fase 2 — API Core (Concluída)

### Arquivos criados

| Arquivo | Descrição |
|---------|-----------|
| [deps.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/deps.py) | Supabase clients (admin/anon), auth JWT, tenant DI |
| [auth.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/middleware/auth.py) | Middleware: verifica JWT em rotas protegidas |
| [tenant.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/middleware/tenant.py) | Middleware: injeta tenant_id no request.state |
| [rate_limit.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/middleware/rate_limit.py) | Rate limit in-memory (100 req/min por IP) |
| [auth router](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/auth.py) | Login, register (cria tenant+profile), refresh |
| [products router](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/products.py) | Import GTIN (via job), listagem, detalhe |
| [jobs router](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/jobs.py) | Listagem e detalhe com eventos |
| [listings router](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/listings.py) | Listagem, publish (via job), approve |
| [discovery router](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/discovery.py) | Stub MVP |
| [main.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/main.py) | FastAPI factory + CORS + 3 middlewares + 5 routers |

### 19 Rotas Registradas

```
POST   /auth/login
POST   /auth/register
POST   /auth/refresh
POST   /products/import
GET    /products
GET    /products/{id}
GET    /jobs
GET    /jobs/{id}
GET    /listings
GET    /listings/{id}
POST   /listings/{id}/publish
POST   /listings/{id}/approve
GET    /discovery/opportunities
GET    /         (health)
GET    /health
```

### Verificação

- ✅ Todos os módulos importam sem erro (Python 3.9)
- ✅ 19 rotas registradas na FastAPI app
- ✅ Corrigidos: MRO `CopyTemplate`, type hints `Optional[str]`

---

## Próximos Passos → Fase 3

```
Fase 3 — Pipeline GTIN
  [ ] apps/api/services/gtin_resolver.py  (GS1 + CNP + cache)
  [ ] apps/api/services/ml_scraper.py     (Mercado Livre data)
  [ ] apps/api/services/copy_generator.py (template → AI fallback)
  [ ] Worker jobs: product.import, product.resolve, listing.generate
```
