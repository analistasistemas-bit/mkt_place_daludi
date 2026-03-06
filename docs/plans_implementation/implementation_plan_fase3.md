# Fase 3 — Pipeline GTIN — Plano de Implementação

**Objetivo:** Implementar todos os services do pipeline de geração de anúncios com ordem obrigatória: `rules → templates → cache → vector reuse → AI`.

**Princípio:** IA é **último recurso**. Lógica determinística primeiro.

---

## Task 1: Services de Infraestrutura (stubs com interface)

**Arquivos:**
- `apps/api/services/gs1_service.py` — `lookup_by_gtin`, `validate_gtin_owner` (stub funcional)
- `apps/api/services/ml_service.py` — `search_similar_listings`, [publish_listing](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/listings.py#109-198), `update_price`, `update_stock` (stub funcional)
- `apps/api/services/llm_service.py` — `batch_polish_listings`, `rewrite_compliance_spans`, `compress_title` (batching 10-30, stub)
- `apps/api/services/vector_service.py` — `embed_text`, `find_similar_copies`, `save_approved_copy` (stub com interface pgvector)

---

## Task 2: Normalizer + Identity Resolver

**Arquivos:**
- `apps/api/services/normalizer.py` — normalização de atributos (limpa HTML, padroniza unidades, title case)
- `apps/api/services/identity_resolver.py` — score de confiança do produto (campos preenchidos, fontes, evidências)

---

## Task 3: Pricing

**Arquivo:** `apps/api/services/pricing.py`
- Cálculo de preço baseado em concorrência (dados do ml_service)
- Margem mínima configurável por tenant
- Fallback para custo + margem padrão

---

## Task 4: Template Renderer (3 categorias)

**Arquivo:** `apps/api/services/template_renderer.py`
- Renderização de templates Jinja2-like por categoria
- 3 categorias: eletrônicos, casa, beleza
- Busca template no banco → fallback para template built-in
- Versionamento de templates

---

## Task 5: Listing Builder + Compliance Rules

**Arquivos:**
- `apps/api/services/listing_builder.py` — monta ListingDraft determinístico (product + template + pricing)
- `apps/api/services/compliance_rules.py` — regex + termos proibidos + marcação de spans para rewrite

---

## Task 6: Pipeline Orchestrator + [__init__.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/packages/shared/__init__.py)

**Arquivos:**
- `apps/api/services/pipeline.py` — orquestrador que executa o fluxo completo: rules → templates → cache → vector → AI
- [apps/api/services/__init__.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/__init__.py) — exports

---

## Verificação

- Importar todos os services sem erro
- Testar pipeline com dados mock (produto fake → listing draft)
