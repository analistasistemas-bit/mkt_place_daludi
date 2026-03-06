# Fase 5 — Frontend MVP (Next.js) — Plano de Implementação

**Objetivo:** Construir a interface web (Next.js App Router + shadcn/ui + Tailwind) da aplicação, com foco em autenticação server-side, dashboards e fluxos baseados na interação com o Worker (Fase 4) e Pipelines de API (Fases 2 e 3).

---

## 1. Setup Técnico e Base (Tasks 1 e 2)
**Arquitetura:** `apps/web/`
- Geração da base do App Router `create-next-app` (TypeScript, Tailwind).
- Inicializar `shadcn-ui@latest`.
- Auth integration (Server-Side) usando `@supabase/ssr` (`middleware.ts` para proteção de rotas `/dashboard`).
- Geração de API Client em `/lib/api-client.ts` para recuperar o JWT do middleware e se comunicar com o container da FastAPI.

---

## 2. Layouts e Fluxos Críticos (Tasks 3 e 4)

### Componentes de Navegação
- `Navbar` top level com profile / logout button.
- `Sidebar` desktop / drawer-mobile com links de navegação persistentes:
  - Importação
  - Produtos
  - Monitor de Jobs
  - Discovery

### Telas
- **Página de Login (`/login`)**: Autenticação Server Action (Supabase SignIn).
- **Importação (`/dashboard/import`)**: Form textual area "Cole uma lista de GTINs" que simula processamento em batch, ativando job `product.import` e disparando Toast Notification.
- **Painel de Jobs (`/dashboard/jobs`)**: Fetch na tabela `job_events` (via API FastAPI). Renderiza tabela estilo ShadCN com status badges coloridos (pending, processing, failed, etc).

---

## 3. Human-In-The-Loop Hero Feature (Task 5)

**Página Lado-a-Lado (`/dashboard/review/[id]`)**
Esta é a joia da coroa da revisão do produto orquestrada pela ML:

1. **Coluna Esquerda (Os Dados)**
   - Display/Form contendo propriedades levantadas pelas Regras de Compliance (Fase 3). 
   - Campos de preço sugerido e Título Gerado.
   - Navegação do usuário nestas propriedades usando *Tabs* de UI.

2. **Coluna Direita (O Preview Comercial)**
   - Um cartão estilizado emulando a cor UI amarela clássica do Mercado Livre com `Badge Mercado Líder`, simulação de fotos renderizadas e Call-to-actions de "Comprar Agora", possibilitando revisar a *Copy* redigida pela LLM vs Contexto visual de Marketing Real.

3. **Aprovação**
   - Um botão `Primary` chamando Endpoint `<FAST_API_URL>/listings/{id}/publish`. Muda a listagem no banco para `published` gerando URL de ML real caso a API Fake/Stub do ML responda OK.

---

## Verificação e Qualidade
- Todos os endpoints chamam o Fast API por Client Component fetch *ou* Server-rendered dependendo do sigilo ou iteratividade.
- Middleware da UI bloqueia usuários não logados de ver previews de anúncios.
