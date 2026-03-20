# Google Search Enrichment Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Melhorar a busca de informações de produtos via GTIN priorizando o Google, com suporte a uma API de busca (Serper.dev) e um scraper de fallback aprimorado.

**Architecture:** O `EnrichmentService` será refatorado para incluir uma cascata interna de busca no Google. Utilizaremos o padrão de "Strategy" implícito: se houver API Key, usa a API; caso contrário, usa o Scraper v2 com headers rotativos.

**Tech Stack:** Python, httpx, regex, pytest.

---

### Task 1: Adicionar Configuração de API ao Ambiente

**Files:**
- Modify: `.env.example`

**Step 1: Adicionar variáveis de ambiente para busca**
Adicionar `SERPER_API_KEY=` ao final do arquivo.

**Step 2: Verificar alteração**
`cat .env.example`

**Step 3: Commit**
```bash
git add .env.example
git commit -m "config: add SERPER_API_KEY to env example"
```

---

### Task 2: Criar Testes para o EnrichmentService

**Files:**
- Create: `tests/services/test_enrichment_service.py`

**Step 1: Escrever teste de falha (TDD)**
Verificar se o serviço de enriquecimento chama o Google.

**Step 2: Executar teste**
`pytest tests/services/test_enrichment_service.py`

**Step 3: Commit**
```bash
git add tests/services/test_enrichment_service.py
git commit -m "test: add initial tests for enrichment service"
```

---

### Task 3: Refatorar EnrichmentService para Priorizar Google

**Files:**
- Modify: `apps/api/services/enrichment_service.py`

**Step 1: Implementar _search_google como prioridade 1**
Mover a chamada do Google para o topo do método `search_product_on_internet`.

**Step 2: Melhorar o Scraper do Google (v2)**
Implementar User-Agents rotativos e Regex mais abrangente.

**Step 3: Implementar _search_google_api (Serper.dev)**
Adicionar lógica para usar a API se a chave estiver presente.

**Step 4: Validar com testes**
`pytest tests/services/test_enrichment_service.py`

**Step 5: Commit**
```bash
git add apps/api/services/enrichment_service.py
git commit -m "feat: refactor enrichment service to prioritize and improve google search"
```
