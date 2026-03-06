# Tarefas — Fase 3 (Pipeline GTIN)

## Planejamento
- [x] Criar plano de implementação
- [x] Aprovação do plano

## Task 1 — Services de Infra (stubs)
- [x] [gs1_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/gs1_service.py) (lookup_by_gtin, validate_gtin_owner)
- [x] [ml_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/ml_service.py) (search_similar, publish, update_price/stock)
- [x] [llm_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/llm_service.py) (batch_polish, rewrite_compliance, compress_title)
- [x] [vector_service.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/vector_service.py) (embed_text, find_similar, save_approved)

## Task 2 — Normalizer + Identity Resolver
- [x] [normalizer.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/normalizer.py) (limpa HTML, padroniza unidades, title case)
- [x] [identity_resolver.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/identity_resolver.py) (score de confiança, fontes, evidências)

## Task 3 — Pricing
- [x] [pricing.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/pricing.py) (concorrência, margem mínima, fallback custo+margem)

## Task 4 — Template Renderer
- [x] [template_renderer.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/template_renderer.py) (3 categorias built-in, banco, versionado)

## Task 5 — Listing Builder + Compliance
- [x] [listing_builder.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/listing_builder.py) (monta ListingDraft determinístico)
- [x] [compliance_rules.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/compliance_rules.py) (regex, termos proibidos, marcação spans)

## Task 6 — Pipeline Orchestrator
- [x] [pipeline.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/pipeline.py) (rules → templates → cache → vector → AI)
- [x] [__init__.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/packages/shared/__init__.py) (exports)

## Verificação
- [x] Todos os 11 services importam sem erro
- [x] Normalizer: HTML clean, unidades, title case
- [x] Identity Resolver: score 0.74 (resolved)
- [x] Compliance: 4 issues em texto problemático
- [x] GS1: GTIN válido com dígito verificador
- [x] Pricing: R$ 901.55 competitivo
- [x] Pipeline: 8 stages, AI SKIPPED, status=ready
