# Walkthrough — Fases 1, 2, 3 & 4 ✅

## Fase 1 — Base (Concluída)
Monorepo, banco Supabase (15 tabelas + pgvector + RLS), schemas Pydantic, infra Docker.

## Fase 2 — API Core (Concluída)
19 rotas FastAPI, 3 middlewares (auth, tenant, rate_limit), 5 routers.

## Fase 3 — Pipeline GTIN (Concluída) 
11 services implementados, incluindo ML, LLM, Vector, Normalizer e Pipeline Orchestrator determinístico. O LLM atua sob demanda quando verificação de compliance exige refatoramento. Ordem de regras rígida.

---

## Fase 4 — Arquitetura de Worker (Concluída) ✅

Os workers foram desenhados desacoplados da web API. Focamos em resiliência e processamentos assíncronos via sub-tarefas no Redis Queues (RQ).

### Infra Core e Resiliência
Módulo [apps/worker/core.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/core.py) foi introduzido contendo decorators universais:
- `@handle_job_lifecycle`: Transita o estado do Job entre `processing`, `completed` e `failed`. Na falha fatal cadastra um DLQ (Dead Letter Queue) virtual através da tabela `job_events`.
- `@with_retry`: Wrapper com exponential backoff e Full-Jitter mitigando thundering herd ao religar com terceiros.

### A Jornada de um Produto Assíncrono (Job Flow)
1. **Importação (`product.import`)**: Disparado pelos arquivos CSV ou submissões via API, ele divide em múltiplos GTINs na conta do *tenant*, validando idempotência antes de gerar a task seguinte.
2. **Resolução (`product.resolve`)**: Converte input inicial usando o `GS1 Service` na confiança via Identity Resolver, gravando no Supabase.
3. **Geração Mágica (`listing.generate`)**: Evoca toda orquestração criada na **Fase 3** (O poderoso módulo [Pipeline](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/services/pipeline.py#37-315)), que roda template matching, pricing analitics contra ML, compliance sem LLM e fallbacks. Salva na database em status `ready`.
4. **Publicação (`listing.publish`)**: Atuando com status real-ready, bate diretamente contra as API do ML para formalizar a listagem e resgatar o ID permanente no mercado livre.

**Extras**: Há também o `discovery_job` que simula um scanner stub das oportunidades futuras de anúncio.

### Resultados de Validação
- Jobs importam de maneira saudável. 
- O simulador de Retry operou com `delay 0.1s` confirmando repasses ao invés de kill instantâneo quando uma "rede falha" em background. Log de Exceção fatal preenche o DLQ sem comprometer o RQ entrypoint principal.

---

## Próximos Passos → Fase 5

```
Fase 5 — Frontend MVP (Next.js)
  [ ] Login form (Supabase Auth proxy)
  [ ] Lista de Produtos / Upload GTIN e tabelas iterativas
  [ ] Visualização e Aprovação de Annúncios
  [ ] Stub do Discovery Dashboard
```
