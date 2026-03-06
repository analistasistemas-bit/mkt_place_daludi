# CLAUDE.md

> Lido automaticamente pelo Claude Code em cada sessão.
> Consolida: Promptfull.md + AGENTS.md + DIRECTIVES.md

---

## Missão do Projeto

SaaS para geração e publicação automatizada de anúncios no **Mercado Livre**.
Entrada principal: **GTIN**. Pipeline: determinístico primeiro, IA apenas como último recurso.

---

## Stack Obrigatória

| Camada       | Tecnologia                              |
|--------------|-----------------------------------------|
| Frontend     | Next.js / React → deploy Vercel         |
| API          | FastAPI (Python 3.11+) → deploy Render  |
| Worker       | Python + RQ (Redis) → deploy Render     |
| Banco        | Supabase (Postgres + RLS + pgvector)    |
| Fila         | Redis (Render Redis ou Upstash)         |
| Auth/Storage | Supabase Auth + Supabase Storage        |

---

## Estrutura do Monorepo

```
/
├── apps/
│   ├── api/          # FastAPI
│   ├── worker/       # Worker RQ
│   └── web/          # Next.js
├── packages/
│   └── shared/       # Schemas Pydantic, utils, logging, config
├── supabase/
│   ├── schema.sql
│   ├── rls.sql
│   └── seeds.sql
├── docs/
│   ├── architecture.md
│   ├── contracts.md
│   ├── api-openapi.yaml
│   ├── setup-local.md
│   └── deploy.md
├── docker-compose.yml
├── .env.example
├── Makefile
└── README.md
```

---

## Ordem de Execução (Pipeline)

```
rules → templates → cache → vector reuse → AI
```

Nunca inverter essa ordem. IA é **sempre** o último fallback.

---

## Fluxo MVP (Agent 1)

```
import GTIN
  → resolve produto (GS1/CNP/Verified)
  → normaliza atributos
  → identity resolver (confiança)
  → concorrência ML (search_similar_listings)
  → precificação
  → template determinístico
  → compliance rules (regex + spans)
  → gate: precisa de LLM?
      NÃO → ListingDraft pronto
      SIM → LLM batch polish (apenas spans marcados)
  → revisão humana
  → publicar ML
```

Discovery (Agent 2): **stub apenas no MVP** — tabela `opportunities` + endpoint GET + UI básica.

---

## Contratos Centrais (Pydantic / JSON Schema)

Definidos em `packages/shared/schemas.py`. São a fonte de verdade.

| Contrato              | Status      | Campos-chave                              |
|-----------------------|-------------|-------------------------------------------|
| `ProductResolved`     | obrigatório | status: RESOLVED \| NEEDS_REVIEW \| BLOCKED |
| `ListingDraft`        | obrigatório | idempotency_key, tenant_id, version       |
| `ListingReady`        | obrigatório | derived from ListingDraft + compliance OK |
| `JobEvent`            | obrigatório | job_id, tenant_id, status, timestamps     |
| `DiscoveryOpportunity`| stub MVP    | id, tenant_id, gtin, score                |

**Nunca quebrar contratos existentes sem atualizar docs/contracts.md e manter backward compat.**

---

## Endpoints MVP

```
POST   /auth/login
POST   /products/import       # planilha CSV/XLSX ou lista de GTINs
GET    /products
GET    /products/{id}
GET    /jobs/{id}
GET    /listings
POST   /listings/{id}/publish
GET    /discovery/opportunities  # stub
```

Todos exigem: **JWT + tenant middleware + rate limit básico**.

---

## Jobs (Worker RQ)

| Job                  | Descrição                          |
|----------------------|------------------------------------|
| `product.import`     | processa planilha/gtins            |
| `product.resolve`    | GS1 lookup + normalização          |
| `listing.generate`   | template + compliance + gate LLM   |
| `listing.publish`    | publica no ML via ml_service       |
| `discovery.scan`     | stub                               |

Todos os jobs devem implementar: **retry + backoff exponencial com jitter + DLQ + idempotência**.

---

## Serviços e Responsabilidades

```
apps/api/services/
├── ml_service.py         # search_similar_listings, publish_listing, update_price, update_stock
├── gs1_service.py        # lookup_by_gtin, validate_gtin_owner (adaptável/placeholder)
├── enrichment_service.py # Google enrichment — apenas campos curtos, nunca textão
├── normalizer.py         # normalização de atributos
├── identity_resolver.py  # score de confiança do produto
├── pricing.py            # cálculo de preço baseado em concorrência
├── template_renderer.py  # templates por categoria, versionados (mín. 3: eletrônicos, casa, beleza)
├── listing_builder.py    # monta ListingDraft determinístico
├── compliance_rules.py   # regex + lista termos arriscados + marcação de spans
├── llm_service.py        # batch_polish_listings, rewrite_compliance_spans, compress_title
└── vector_service.py     # embed_text, find_similar_copies, save_approved_copy
```

**Regra absoluta:** controllers e workers nunca chamam APIs externas diretamente. Sempre via service.

---

## Política de Uso de IA

✅ IA pode ser usada para:
- polimento de texto (`batch_polish_listings`)
- reescrita de compliance (`rewrite_compliance_spans`)
- compressão de título (`compress_title`)

❌ IA nunca decide:
- fatos do produto
- preço
- lógica de negócio

**Batching obrigatório:** 10–30 itens por chamada LLM, agrupados por categoria.
**Cache agressivo:** se só preço/estoque mudou → sem LLM.
**Vector reuse:** copies aprovadas armazenadas em pgvector e reaproveitadas.

---

## Banco de Dados (Supabase)

Tabelas principais:
```
tenants, users/profiles, products, product_sources, product_evidence,
listings, listing_versions, jobs, job_events, copy_templates,
vector_embeddings, llm_cache, audit_logs, caches, opportunities
```

Regras:
- Todo registro deve ter `tenant_id`
- RLS ativo em todas as tabelas (policies em `supabase/rls.sql`)
- **Nunca bypassar tenant isolation**
- `pgvector` extension habilitada
- Índices em: `gtin`, `tenant_id`, `status`, `created_at`

---

## Multi-Tenancy

- RLS no Postgres por `tenant_id`
- Quotas por tenant (configurável)
- Rate limit por tenant e por integração
- Middleware de tenant obrigatório em todos os endpoints

---

## Observabilidade

Todo log deve incluir:
```json
{
  "tenant_id": "...",
  "job_id": "...",
  "service": "...",
  "level": "info|error|warn",
  "message": "..."
}
```

Usar logging estruturado JSON em Python. Nunca logar credenciais ou dados sensíveis.

---

## Comandos Essenciais

```bash
make dev          # sobe api + worker + redis (docker-compose)
make migrate      # aplica schema.sql no Supabase
make seed         # roda seeds.sql
make lint         # ruff + black + mypy (Python) | eslint + prettier (JS)
make test         # roda suite de testes
make deploy-api   # deploy Render (API)
make deploy-worker # deploy Render (Worker)
make deploy-web   # deploy Vercel (Web)
```

---

## Variáveis de Ambiente (nunca commitar valores reais)

```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

# Redis
REDIS_URL=

# Mercado Livre
ML_CLIENT_ID=
ML_CLIENT_SECRET=
ML_REDIRECT_URI=

# LLM
LLM_PROVIDER=          # openai | anthropic | etc
LLM_API_KEY=
LLM_MODEL=

# Embeddings
EMBEDDINGS_PROVIDER=   # openai | stub
EMBEDDINGS_API_KEY=

# App
API_SECRET_KEY=
ENVIRONMENT=           # local | staging | production
```

---

## Segurança

- Nunca expor API keys, secrets ou credenciais de banco
- Frontend nunca acessa serviços externos diretamente
- Toda comunicação externa isolada nos services
- Stubs/mocks para integrações sem credencial — manter interface pronta para plugar

---

## Regras para o Agente (resumo operacional)

1. **Antes de criar código:** identificar o módulo correto, checar serviços existentes, verificar compatibilidade com schema.
2. **Antes de criar um novo serviço:** confirmar que não existe lógica equivalente em outro módulo.
3. **Antes de chamar API externa:** garantir que está dentro de um `*_service.py`.
4. **Antes de usar LLM:** confirmar que regras + templates + cache + vector foram tentados.
5. **Antes de mudar contrato:** atualizar `docs/contracts.md` e manter backward compat.
6. **Em caso de dúvida:** solução mais simples, sem novas dependências, preservando consistência.

---

## Fase de Implementação Sugerida

```
Fase 1 — Base
  [ ] Estrutura do monorepo
  [ ] supabase/schema.sql + rls.sql + seeds.sql
  [ ] packages/shared/schemas.py (contratos Pydantic)
  [ ] docker-compose.yml + .env.example + Makefile

Fase 2 — API Core
  [ ] apps/api/main.py + auth middleware + tenant middleware
  [ ] Routers: products, jobs, listings, discovery (stub)
  [ ] Supabase client

Fase 3 — Services
  [ ] normalizer, identity_resolver, pricing
  [ ] template_renderer (3 categorias) + listing_builder
  [ ] compliance_rules
  [ ] ml_service (com stubs para credenciais)
  [ ] gs1_service (placeholder adaptável)
  [ ] llm_service (batch + cache + stub)
  [ ] vector_service (interface + stub embeddings)

Fase 4 — Worker
  [ ] apps/worker/worker.py
  [ ] Job handlers: import, resolve, generate, publish, discovery stub
  [ ] Retry + backoff + DLQ

Fase 5 — Frontend
  [ ] Login, upload planilha, dashboard produtos
  [ ] Tela de jobs, revisão humana, publicar
  [ ] Discovery stub

Fase 6 — Docs & Deploy
  [ ] docs/ completos
  [ ] Configurações Vercel + Render
  [ ] README.md final
```

---

*Gerado a partir de: Promptfull.md + AGENTS.md + DIRECTIVES.md*
