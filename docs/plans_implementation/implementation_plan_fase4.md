# Fase 4 — Worker Implementation — Plano de Implementação

**Objetivo:** Implementar os workers background (RQ) responsáveis por orquestrar o fluxo assíncrono do produto. Integraremos os serviços criados na Fase 3, adicionando resiliência (retry, DLQ) e idempotência.

---

## 1. Infraestrutura do Worker e Resiliência

**Arquivo:** `apps/worker/core.py` (Utilitários base do worker)
- **Retry com Backoff + Jitter:** Decorator customizado para envolver as funções dos jobs.
  - Implementará `exponential backoff` (ex: `base * (2^attempt)`)
  - Adicionará `jitter` (aleatoriedade) para evitar thundering herd.
- **Idempotência:**
  - Checar versionamento no banco (Supabase) ou status atual antes de reprocessar.
- **DLQ (Dead Letter Queue):**
  - Jobs falhos (após limite de retries) são logados/registrados no banco (ex: status `failed` no [jobs](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/jobs.py#70-108)).

**Arquivo:** `apps/worker/worker.py` (Ponto de entrada do RQ)
- Configuração do Worker customizado do RQ conectando ao Redis.
- Setup de `Sentry`/Logging estruturado (já disponível em packages).

---

## 2. Job Handlers (`apps/worker/jobs/`)

### 2.1. Importação de Produto (`product.import`)
**Arquivo:** `apps/worker/jobs/import_job.py`
- Recebe arquivo CSV/XLSX ou lista de GTINs.
- Valida entradas.
- Cria os registros na tabela `products` via Supabase.
- Dispara sub-jobs (`product.resolve`) para cada GTIN válido importado.

### 2.2. Resolução do Produto (`product.resolve`)
**Arquivo:** `apps/worker/jobs/resolve_job.py`
- Executa a ETAPA 1 do pipeline do Fase 3 (Normalizer + Identity).
- Em vez de chamar o pipeline completo de uma vez, aqui pode chamar parcialmente os servicos ou acionar o Pipeline caso o workflow seja monolítico. *No caso, faremos a chamada controlada para salvar os status intermediários.*
- Atualiza o status do `products` no banco.
- Se score ok, enfileira `listing.generate`.

### 2.3. Geração do Anúncio (`listing.generate`)
**Arquivo:** `apps/worker/jobs/generate_job.py`
- Carrega o produto do banco.
- Executa as Etapas 2, 3, 4 e 5 do Pipeline (Templates, Cache, Vector, AI).
- Utiliza a classe `Pipeline` já desenvolvida na Fase 3.
- Salva o `ListingDraft` no banco.
- Caso compliance detecte erro grave (high severity), altera status para `pending_review`. Senão, `ready`.

### 2.4. Publicação do Anúncio (`listing.publish`)
**Arquivo:** `apps/worker/jobs/publish_job.py`
- Carrega o `ListingDraft` pronto com status `ready`.
- Verifica integração (ex: ML OAuth).
- Chama `ml_service.publish_listing()`.
- Se sucesso, muda status para `published`.
- Registra auditoria/events.

### 2.5. Discovery Scan (Stub) (`discovery.scan`)
**Arquivo:** `apps/worker/jobs/discovery_job.py`
- Stub conforme documentação.
- Cria mock de novos GTINs como oportunidades na tabela `opportunities`.

---

## Estratégia de Atualização de Status

- Todos os jobs atualizarão as tabelas `jobs` e `job_events` para manter rastreabilidade.
- Todo processamento usará o cliente de banco `get_supabase_client()` instanciado com permissões apropriadas, ou repassado do context do job.

---

## Verificação
- Criar script de teste que simule a injeção na fila do RQ (Redis) e comprove:
  - Backoff funcionando no caso de erro forçado.
  - Execução correta do job `product.import` encadeado com os demais.
