# Design Document: Frontend MVP (Next.js + shadcn/ui)

## 1. Visão Geral
O Frontend da plataforma servirá como a interface principal de gestão e transparência para o pipeline de geração de anúncios do Mercado Livre. Ele permite upload de GTINs, acompanhamento de processamento assíncrono e aprovação humana dos anúncios gerados ("Human-in-the-Loop").

**Tech Stack:** 
- Framework: Next.js (App Router) + TypeScript
- Estilização: Tailwind CSS
- Componentes: shadcn/ui (Table, Badge, Dialog, Form, Toast, Tabs)
- Autenticação: Supabase Auth (Server-side cookies)
- Consumo API: Serviço de cliente centralizado usando Server Actions / Server Components quando possível, Client Components para interatividade.

## 2. Arquitetura de Rotas (Next.js App Router)

- `/login`: 
  - Login via Supabase Auth.
- `/dashboard`: Layout base contendo Navbar e Sidebar para navegação.
  - `/dashboard/products` (Default): Listagem de produtos importados e gerados.
  - `/dashboard/import`: Tela com formulário para upload de arquivos ou input manual de múltiplos GTINs.
  - `/dashboard/jobs`: Monitoramento dos jobs background do RQ com atualizações de status.
  - `/dashboard/review`: Tela fundamental de edição/aprovação (Human-in-the-Loop). Apresentará o layout **Lado a Lado (Side-by-side)**:
    - **Esquerda:** Dados do Anúncio Gerado (Título, categorias com Tabs de navegação, propriedades, preço sugerido).
    - **Direita:** Preview visual renderizando um simulacro do layout do cartão de anúncio do Mercado Livre.
  - `/dashboard/discovery`: Tela de Oportunidades (Stub)

## 3. Gestão de Estado e Componentes
- `shadcn/ui` é o pilar de UI. A interatividade principal concentra-se nos Forms (React Hook Form + Zod) e Dialogs de Confirmação para evitar ações destrutivas (Ex: "Ativar Anúncio").
- Componentes client-side (marcados com `"use client"`) serão isolados nas camadas de folhas da árvore de componentes, mantendo layouts grossos rodando nos Server Components.

## 4. Integração de API
Toda comunicação do Next.js voltada a regras de negócio passa pela FastAPI (`/apps/api`), orquestrando middlewares de Autenticação e Multi-Tenancy (passando o token JWT do Supabase adiante).

## 5. Fluxo de Decisões do Usuário
- Importar Produto -> Pipeline (Worker) ativado.
- Produto Resolvido e Anunciado na Fase 3 cai na Review queue (`/dashboard/review`).
- Usuário aprova -> Request ao backend FastAPI (`POST /listings/{id}/publish`) -> Worker de Publish assume e devolve Link no ML.
