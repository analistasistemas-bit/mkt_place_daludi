# Walkthrough — Fases 1, 2 & 3 ✅

## Fase 1 — Base (Concluída)
Monorepo, banco Supabase (15 tabelas + pgvector + RLS), schemas Pydantic, infra Docker.

## Fase 2 — API Core (Concluída)
19 rotas FastAPI, 3 middlewares (auth, tenant, rate_limit), 5 routers.

---

## Fase 3 — Pipeline GTIN (Concluída) ✅

### 11 Services Implementados

| Service | Arquivo | Responsabilidade |
|---------|---------|-----------------|
| **GS1** | [gs1_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/gs1_service.py) | Validação GTIN (módulo 10), lookup stub, detecção BR (789/790) |
| **ML** | [ml_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/ml_service.py) | search_similar, publish, update_price/stock (stubs OAuth2-ready) |
| **LLM** | [llm_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/llm_service.py) | batch_polish (10-30 itens), rewrite_compliance, compress_title |
| **Vector** | [vector_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/vector_service.py) | embed_text, find_similar (Jaccard), save_approved (pgvector ready) |
| **Normalizer** | [normalizer.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/normalizer.py) | HTML clean, unidades BR, title case inteligente, dedup imagens |
| **Identity** | [identity_resolver.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/identity_resolver.py) | Score 0-1 com breakdown, pesos por campo e fonte |
| **Pricing** | [pricing.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/pricing.py) | Competitivo (-5%), custo+margem (30%), floor price (10% mín) |
| **Template** | [template_renderer.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/template_renderer.py) | 3 categorias built-in (eletrônicos, casa, beleza), aliases, banco |
| **Compliance** | [compliance_rules.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/compliance_rules.py) | ~30 termos proibidos (ANVISA/PROCON/ML), 5 regex, título rules |
| **Builder** | [listing_builder.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/listing_builder.py) | Monta ListingDraft determinístico, idempotency key, attrs ML |
| **Pipeline** | [pipeline.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/pipeline.py) | Orquestrador: rules → templates → cache → vector → AI |

### Pipeline — Ordem Obrigatória

```
ETAPA 1: RULES
  ├─ normalize (HTML, unidades, title case)
  ├─ identity_resolve (score 0-1)
  └─ gate: score < 0.4 → bloqueado

ETAPA 2: TEMPLATES
  └─ render (tenant → global → built-in)

ETAPA 3: CACHE
  ├─ ML search similar (pricing)
  └─ pricing (competitivo / custo+margem)

ETAPA 4: VECTOR REUSE
  └─ find_similar ≥ 0.85 → reutilizar (zero LLM)

ETAPA 5: AI (ÚLTIMO RECURSO)
  ├─ compliance spans → rewrite via LLM
  ├─ título > 60 chars → compress via LLM
  └─ SE nada necessário → AI SKIPPED ✅
```

### Resultados da Verificação

```
✅ 11 services importam OK
✅ Normalizer: HTML clean, "gramas" → "g", dedup imagens
✅ Identity: score 0.74 (resolved), breakdown por campo
✅ Compliance: 4 issues em texto "MELHOR DO MERCADO milagroso cura (11)99999-9999"
✅ GS1: GTIN 7891234567899 válido (dígito verificador módulo 10)
✅ Pricing: R$ 901.55 competitivo com 3 concorrentes
✅ Pipeline: 8 stages executadas, AI SKIPPED, listing status=ready
```

---

## Próximos Passos → Fase 4

```
Fase 4 — Worker Implementation
  [ ] apps/worker/jobs/ (product.import, product.resolve, listing.generate, listing.publish)
  [ ] Retry + backoff exponencial + jitter + DLQ + idempotência
  [ ] Integração pipeline.py nos workers
```
