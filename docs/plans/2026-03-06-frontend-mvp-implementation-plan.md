# Frontend MVP Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Construir a interface web (Next.js App Router + shadcn/ui + Tailwind) com foco em upload de produtos, visualização de jobs, e tela lado-a-lado de revisão de anúncios.

**Architecture:** Next.js App Router isolando a interface web em `apps/web`. Layout de Dashboard base protegerá rotas via cookies do Supabase.

**Tech Stack:** Next.js, React, Tailwind CSS, shadcn/ui, Supabase SSR, TypeScript, Lucide Icons.

---

### Task 1: Next.js Initialization & Setup

**Files:**
- Create: `apps/web/package.json` e configs associadas via `create-next-app`
- Modify: `packages/shared/` ou similares dependendo das chamadas

**Step 1: Inicializar o projeto App Router**
Rodar `npx create-next-app@latest apps/web --typescript --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm`

**Step 2: Configurar shadcn/ui**
Rodar `cd apps/web && npx shadcn-ui@latest init` (aceitar settings padrão para css variables, stone/slate ou modo dark).

**Step 3: Instalar Componentes shadcn chave**
Rodar `cd apps/web && npx shadcn-ui@latest add table badge dialog form toast tabs card button input label textarea`

**Step 4: Commit**
```bash
git add apps/web
git commit -m "feat: setup next.js app router and shadcn/ui initialized"
```

---

### Task 2: Supabase SSR Auth Setup & API Client

**Files:**
- Create: `apps/web/src/utils/supabase/server.ts`
- Create: `apps/web/src/utils/supabase/client.ts`
- Create: `apps/web/src/utils/supabase/middleware.ts`
- Create: `apps/web/src/middleware.ts`
- Create: `apps/web/src/lib/api-client.ts`

**Step 1: Instalar dependências SSR**
Rodar `npm install @supabase/ssr @supabase/supabase-js` em `apps/web`.

**Step 2: Escrever helpers SSR Supabase**
Implementar `server.ts` e `client.ts` segundo doc oficial `@supabase/ssr` (basecookies config).

**Step 3: Criar Middleware de Borda**
Em `middleware.ts`, proteger `/dashboard` exigindo sessão ativa via `supabase.auth.getUser()`. Se deslogado, rewrite/redirect para `/login`.

**Step 4: Criar API Client Central**
Em `api-client.ts`, utilitário `fetchApi(endpoint, options)` que resgata credenciais geradas do Supabase no Server environment (cookies) e injeta no cabeçalho Authorization: Bearer.

**Step 5: Commit**
```bash
git add apps/web/src/utils apps/web/src/middleware.ts apps/web/src/lib/api-client.ts
git commit -m "feat: setup supabase ssr, middleware roteamento protegido e api-client interceptor"
```

---

### Task 3: Layout Core & Navigation & Login

**Files:**
- Create: `apps/web/src/app/login/page.tsx`
- Create: `apps/web/src/app/dashboard/layout.tsx`
- Create: `apps/web/src/components/layout/sidebar.tsx`
- Create: `apps/web/src/components/layout/navbar.tsx`

**Step 1: Criar Tela de Login Simples**
Em `login/page.tsx`, Form básico batendo em uma *Server Action* que lida com `supabase.auth.signInWithPassword`. Ao ter sucesso, redirect para `/dashboard`.

**Step 2: Painel e Layout do Dashboard**
Desenvolver estrutura de HTML `flex-col md:flex-row h-screen` com um Sidebar à esquerda (Links: Products, Import, Jobs, Discovery) e Navbar top header (com botões de log out).

**Step 3: Commit**
```bash
git add apps/web/src/app/login apps/web/src/app/dashboard/layout.tsx apps/web/src/components/layout
git commit -m "feat: tela de auth e base layout do painel administrativo"
```

---

### Task 4: Fluxos Básicos de Importação e Painel

**Files:**
- Create: `apps/web/src/app/dashboard/import/page.tsx`
- Create: `apps/web/src/app/dashboard/page.tsx` (Lista de produtos)
- Create: `apps/web/src/app/dashboard/jobs/page.tsx`

**Step 1: Import Page UI**
`import/page.tsx` - Form simples com Textarea batendo na view da FastAPI (mock da ingestão via CSV ou GTINs em batch). Display com *Toast* confirmando batch disparado no Worker.

**Step 2: Tabela de Jobs Progress**
`jobs/page.tsx` - Server component buscando de `GET /jobs` ou lista de eventos (usando shadcn Table). Mapear enums para Badges `pending (gray)`, `processing (blue)`, `completed (green)`, `failed (red)`.

**Step 3: Commit**
```bash
git add apps/web/src/app/dashboard*
git commit -m "feat: constroi telas estáticas import/jobs com server requests"
```

---

### Task 5: Tela Side-by-Side de Review Hero Feature

**Files:**
- Create: `apps/web/src/app/dashboard/review/[id]/page.tsx`
- Create: `apps/web/src/components/review/ProductDetailsColumn.tsx`
- Create: `apps/web/src/components/review/MarketplacePreviewColumn.tsx`

**Step 1: Página Mãe (Routing & Grid)**
Em `review/[id]/page.tsx`, instanciar grid: `grid grid-cols-1 md:grid-cols-2 gap-4`. Carregar os dados (via server-side) de *ListingDraft* baseado no *ID*. Lidar com status de NotFound.

**Step 2: Coluna da Esquerda (Form/Dado Gerado)**
Construir formulários ou displays baseados em abas `Tabs`. (Geral, Preço, Dimensões, Descrição). Permitir que o revisor edite o cache finalizado. Exibir confiancia de AI (score the GS1).

**Step 3: Coluna Direita (Mercado Livre Preview Simulacro)**
Card emulando as divs amarelinhas/brancas modernas com Badge "Mercado Líder" falso e o preço realçadíssimo, fotos via render básico e mockup real de como fica a página de vendas. Isso provê grande visibilidade do template escolhido na Fase 3.

**Step 4: Ação de 'Aprovar e Publicar'**
Botão verde forte que aciona request via Client Components batendo no endpoint da FastAPI (`POST /listings/{id}/publish`) passando a configuração confirmada. Toast success!

**Step 5: Commit finalização**
```bash
git add .
git commit -m "feat: complete next.js frontend application module"
```
