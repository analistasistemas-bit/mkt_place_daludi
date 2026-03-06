# API Contracts

Toda a negociação de dados, Request/Response payloads e Tipos centrais do banco residem no núcleo partilhado em `packages/shared/schemas.py`.

A fonte de tipagem deve sempre guiar as assinaturas de View (FastAPI) e dos Modelos (Next.js TypeScript).

## Modelos Centrais

| Modelo | Status Schema | Responsabilidade | Contém |
|---|---|---|---|
| `ProductResolved` | Fundamental | Atividade de Fase Inicial e GS1 Pipeline. | `['imported', 'resolving', 'resolved', 'needs_review', 'blocked']` e pontuação ML `confidence [0-1]`. |
| `ListingDraft` | Fundamental | Escrita após passar os 6 estagios determinísticos (Fase 3). | Template IDs, Categoria Alvo sugerida, descritivo, preço ponderado por metríca de ML + Regras base da Store API. |
| `JobEvent` | Analítico | Mantém Worker e Tela de Logs vivos com feedback iterativo pra cada tarefa MQ disparada. | `tenant_id`, `job_id`, `message` e status. |
| `DiscoveryOpportunity` | Stubbed MVP | Provisões de produtos ainda não integrados identificados pela AI buscando lacunas de catálogo no ML (Competitor Tracker). | Mock com score (%). |

## Princípios de Mutabilidade API
- Nenhum desenvolvedor deve quebrar retrocompatibilidade nas rotas estritas (Listadas na doc de Design / Swagger). 
- Caso seja vital acionar um novo campo obrigatório a Web Front terá de ser re-compilada, atrase o envio dos enums pros pipelines até haver sync de release version via Docker `latest` tag com os pods Web da Vercel. 
- O Fastapi devolve o Strict mode do Pydantic em *Bad Request (422)*. O Next.js usa Typescript interfaces que simulam os modelos nativamente.
