# Checklist de Deploy - Marketplace SaaS

Este documento contém o passo a passo e todas as variáveis de ambiente necessárias para realizar o deploy manual na plataforma Render (backend/worker) e Vercel (frontend).

## 1. Render - API Web Service (`mktplace-api`)

Crie um novo **Web Service** no Render com as seguintes configurações:

- **Nome:** `mktplace-api`
- **Region:** Oregon (Ou a de sua preferência)
- **Branch:** `main`
- **Root Directory:** (Deixe em branco ou aponte para a raiz do repositório)
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`

### Variáveis de Ambiente (Environment)

| Chave | Valor |
|-------|-------|
| `SUPABASE_URL` | `https://cuetfuxvxzlyhienpafc.supabase.co` |
| `SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1ZXRmdXh2eHpseWhpZW5wYWZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI3NTkyNjUsImV4cCI6MjA4ODMzNTI2NX0.fJ0OF9ABl86TvQ82jKTy3GwkOx-ROX23SWnZd-7nxhA` |
| `SUPABASE_SERVICE_ROLE_KEY` | `<COLE_AQUI_A_SERVICE_ROLE_KEY_DO_SUPABASE>` |
| `REDIS_URL` | `rediss://default:AbSbAAIncDJlMjdkMjAzYjU0NTU0MWFhYmI5MmEwZTYwMWM4MGViNnAyNDYyMzU@mutual-feline-46235.upstash.io:6379` |
| `API_SECRET_KEY` | `production-secret-key-mktplace` |
| `ENVIRONMENT` | `production` |
| `LLM_PROVIDER` | `stub` |
| `LLM_API_KEY` | `<LLM_API_KEY_PLACEHOLDER>` |
| `LLM_MODEL` | `gpt-4o-mini` |
| `EMBEDDINGS_PROVIDER` | `stub` |
| `EMBEDDINGS_API_KEY` | `<EMBEDDINGS_API_KEY_PLACEHOLDER>` |
| `ML_CLIENT_ID` | `<ML_CLIENT_ID_PLACEHOLDER>` |
| `ML_CLIENT_SECRET` | `<ML_CLIENT_SECRET_PLACEHOLDER>` |
| `ML_REDIRECT_URI` | `https://seu-dominio.com/api/ml/callback` |
| `WORKER_CONCURRENCY` | `4` |
| `WORKER_QUEUES` | `default,high,low` |

---

## 2. Render - Worker Web Service (`mktplace-worker`)

Crie um novo **Web Service** (Plano Free) no Render com as seguintes configurações:

- **Nome:** `mktplace-worker`
- **Region:** A mesma da API
- **Branch:** `main`
- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python -m http.server $PORT & python -m rq worker --url $REDIS_URL default high low`

### Variáveis de Ambiente (Environment)

Dê preferência para usar "Environment Groups" no Render e compartilhar variáveis, ou copie as necessárias:

| Chave | Valor |
|-------|-------|
| `SUPABASE_URL` | `https://cuetfuxvxzlyhienpafc.supabase.co` |
| `SUPABASE_SERVICE_ROLE_KEY` | `<COLE_AQUI_A_SERVICE_ROLE_KEY_DO_SUPABASE>` |
| `REDIS_URL` | `rediss://default:AbSbAAIncDJlMjdkMjAzYjU0NTU0MWFhYmI5MmEwZTYwMWM4MGViNnAyNDYyMzU@mutual-feline-46235.upstash.io:6379` |
| `ENVIRONMENT` | `production` |
| `LLM_PROVIDER` | `stub` |
| `LLM_API_KEY` | `<LLM_API_KEY_PLACEHOLDER>` |
| `WORKER_CONCURRENCY` | `4` |
| `WORKER_QUEUES` | `default,high,low` |

---

## 3. Vercel - Frontend Web (`apps/web`)

Importe o repositório na Vercel e configure:

- **Framework Preset:** Next.js
- **Root Directory:** `apps/web`
- **Build Command:** `npm run build`
- **Install Command:** `npm install`

### Variáveis de Ambiente (Environment)

| Chave | Valor |
|-------|-------|
| `NEXT_PUBLIC_SUPABASE_URL` | `https://cuetfuxvxzlyhienpafc.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | `eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImN1ZXRmdXh2eHpseWhpZW5wYWZjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI3NTkyNjUsImV4cCI6MjA4ODMzNTI2NX0.fJ0OF9ABl86TvQ82jKTy3GwkOx-ROX23SWnZd-7nxhA` |
| `NEXT_PUBLIC_API_URL` | `https://mktplace-api.onrender.com` *(Altere para a URL correta após o deploy do Web Service renderizado)* |
