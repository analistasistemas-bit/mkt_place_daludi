# Plano de Implementação: Correção de Resolução de GTIN e Enriquecimento

Este documento descreve as alterações necessárias para resolver o problema de GTINs que não trazem o "nome base" (título) nem a confiança correta, além de corrigir bugs no worker.

## 1. Problemas Identificados
- **Erro de Regex no Enrichment**: O `enrichment_service.py` possui um bug em uma regex que causa `re.error` devido à posição da flag `(?i)`. Isso impede o fallback de busca na internet quando as bases nacionais (Brasil API/OFF) falham.
- **Idempotência Agressiva**: O `resolve_job.py` pula a resolução se o produto tiver um título, ignorando o fato de que o título pode ser apenas um placeholder de fallback (ex: "GTIN... - Aguardando Identificação").
- **Falha de Dados Externos**: O GTIN `7891020400320` especificamente não consta na Brasil API nem no OpenFoodFacts, tornando o fix do Enrichment Service crucial.

## 2. Alterações Propostas

### 2.1. Enrichment Service (`apps/api/services/enrichment_service.py`)
- Corrigir a regex no método `_process_matches`:
  - **De**: `re.sub(r'[\s\-\|\:\.]+$(?i)', '', clean_title)`
  - **Para**: `re.sub(r'(?i)[\s\-\|\:\.]+$', '', clean_title)`
- Garantir que a flag `(?i)` esteja no início para compatibilidade com Python 3.11+.

### 2.2. Resolve Job (`apps/worker/jobs/resolve_job.py`)
- Refinar a lógica de substituição de títulos.
- Na verificação de idempotência (pular job), considerar títulos que começam com "GTIN" como inválidos/substituíveis, forçando a re-resolução se o status for `pending` ou se o usuário estiver forçando a importação.

### 2.3. Publish Job (`apps/worker/jobs/publish_job.py`)
- Verificar se restam chamadas a `.get()` no objeto `MLPublishResult` (embora commits anteriores indiquem que já foi tratado, faremos uma revisão final para garantir estabilidade).

## 3. Fluxo de Verificação
1. Aplicar correções.
2. Reiniciar o worker (via deploy no Render).
3. Testar a importação do GTIN `7891020400320`.
4. Verificar se o status muda para `resolved` ou `needs_review` com título real vindo da busca (ex: DuckDuckGo).

## 4. Próximos Passos
- Executar plano via `writing-plans`.
