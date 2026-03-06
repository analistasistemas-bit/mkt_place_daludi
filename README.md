# Daludi Marketplace AI 

Plataforma inteligente B2B SaaS para Geração, Importação e Sincronização Enriquecida de Anúncios no Mercado Livre, suportada por orquestração de Inteligência Artificial Determinística e Background Workers de alta resiliência.

![Next.js](https://img.shields.io/badge/Front_End-Next.js_15-black?style=flat&logo=next.js&labelColor=000)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&labelColor=000)
![Supabase](https://img.shields.io/badge/DB_e_Auth-Supabase-3ECF8E?style=flat&logo=supabase&labelColor=000)
![Redis](https://img.shields.io/badge/Worker_Queue-Redis_RQ-DC382D?style=flat&logo=redis&labelColor=000)

---

## 📖 Arquitetura do Produto

Este projeto utiliza uma arquitetura limpa de **Monorepo** rodando sobre orquestrações Serverless/PaaS:

1. **`apps/api/` (FastAPI Core):** O Gateway sincrono de leitura, RLS Tenants e manipulação de Status. Recebe dados do Client e da Filas. Funciona usando o ecosistêsma do Supabase API Auth.
2. **`apps/worker/` (RQ Python):** O "músculo". Executa as integrações lentas externas. O Pipeline passa pelo Normalizer, GS1, templates rígidos base, Vector DB Cache Reuse e LLM Generation de Cópys/SEO para criação perfeita do produto via MercadoLivre.
3. **`apps/web/` (Next.js 15):** SSR Frontend em Edge para experiência "Apple-like". UI componentizada em Tailwind + shadcn/ui.
4. **`packages/shared/`:** Schemas PyDantic e interfaces Typescript.

Para aprofundamento de domínios, verifique:
* [Arquitetura](/docs/architecture.md)
* [Contratos de API](/docs/contracts.md)
* [Swagger OpenAPI](/docs/api-openapi.yaml)

---

## 🚀 Como Iniciar

**1. Setup das Variáveis e Banco de Dados**
Toda autenticação e tabela primária repousa num Supabase PostgreSQL com a extensão `pgvector`.
Prepare o Supabase com as schemas primordiais contidas na pasta `supabase/` (schema `schema.sql`, auth hooks `rls.sql` e massas de testes `seeds.sql`). 

**2. Guia de Setup Local**
Consulte **[o guia de Local Setup](/docs/setup-local.md)** para instruções de inicialização de `docker-compose.yml`, Makefiles e dependências `pip` / `npm`. O repositório utiliza Multi-terminal Run Commands via `make dev`.

**3. Deploy na Nuvem (Produção)**
Pronto para Vercel e Render nativamente. Para injetar Tokens e preparar os Pods na GCP/AWS/Render acesse **[Instruções de Deploy Oficial](/docs/deploy.md)**. 

---

## 🛠 Comandos Make Úteis
A automação de desenvolvimento reside sob a aba do arquivo raiz `Makefile`.

* `make dev-api` — Subir o uvicorn FastAPI na 8000
* `make dev-worker` — Consumidor RQ atrelado ao localhost:6379 
* `make dev-web` — Levanta o Next.js Web App
* `make supabase-push` — Força alteração do db local para seu Remote Cloud.

### Roadmap de Manutenabilidade
O Produto adere aos fluxos *HitL (Human-in-the-Loop)* em que modelos gerativos nunca sobem anúncios direto sem o Aval do Operador logado na Conta Next.js (Dashboard), priorizando compliance e evitando faturas/warnings excessivos nos Marketplaces por bots.

---
**Build By Daludi Mastermind Protocol**
