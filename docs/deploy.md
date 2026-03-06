# Guia de Deploy Híbrido (Vercel + Render + Supabase)

O Monorepo está preparado com foco em infraestrutura "Serverless/PaaS" para escala zero.

## 1. Supabase (PostgreSQL + Auth + Storage)
Este é o coração dos dados, e rodará nos servidores Enterprise (ou free trial) do próprio Supabase.
1. Crie o novo Project base pela Dashboard web.
2. Certifique-se que o Datawarehouse está na Região desejada (Ex: `us-east-1` ou `sa-east-1` Brasil).
3. Habilite a extensão do Vectores (`create extension if not exists vector;`) abrindo o painel SQL.
4. Execute os scripts core (schema.sql e rls.sql) via Supabase CLI:
   ```bash
   supabase link --project-ref cuetfuxvxzlyhienpafc
   supabase db push
   ```
5. Capture chaves do Projeto. O Supabase já cobre nativamente proteção DDos/Rate Limit na Auth, e RLS previne que chaves vazadas do NEXT_PUBLIC vazem dados restritos.

## 2. Redis (Mensageria da Queues)
Sinta-se livre de utilizar **Render Managed Redis** (pago, atua dentro da VCN no Render) ou o **Upstash REST/Redis** Edge Database (Tier Free robusto e compatível via tcp `redis://`). Pegue a URI final de conexão.

## 3. Render (Backend API e Workers)
É a solução ideal para os containers Python rodarem com eficiência e estabilidade isolados de "Cold Boots" longos do Serverless Lambdas se você deseja previsibilidade e persistencia do Machine Learning model.

**Serviço 1: Web Service (FastAPI)**
1. Dashboard → New Web Service.
2. Link ao repositório GitHub (`mkt_place_ia`).
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn apps.api.main:app --host 0.0.0.0 --port $PORT`
5. Variáveis Necessárias (Inject Environment Variables):
   - `SUPABASE_URL`
   - `SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`
   - `REDIS_URL`
   - `ENVIRONMENT=production`

**Serviço 2: Web Service (RQ Worker no plano Free)**
1. Dashboard → New Web Service.
2. Vincular Repositório.
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `python -m http.server $PORT & python -m apps.worker.worker`
5. Environment Variables:
   - Duplique as mesmas do `Web Service`. Você precisará dos dados do banco para fazer insert.
   - Forneça os tokens stub do (Ex: OpenAI Key `LLM_API_KEY`, etc).
6. O `apps.worker.worker` inicia uma thread de keep-alive que faz `GET https://mktplace-worker.onrender.com/` a cada 4 minutos para evitar o spin-down do plano gratuito durante jobs longos.

## 4. Vercel (Frontend Next.js App Router)
Otimizado de nascença e deploy "One-Click".

1. Acesse o portal Vercel e importe o App web do Repositório do GitHub.
2. Aponte o **Root Directory** do deploy para `apps/web`.
3. Variáveis de Ambiente a Injetar:
   - `NEXT_PUBLIC_SUPABASE_URL` (Sua URL .supabase.co)
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY` (Sua Service API anon Key)
   - `API_URL` (Cole o Hostname gerado do App no Render acima. Ex: `https://mkt-place-api.onrender.com`)

## 5. Automação via Comandos MAKE (CI/CD)
Se atrelar as APIs da Vercel/Render no seu CLI da máquina (`npm i -g vercel`), pode usar as rotinas implementadas:

```bash
# Frontend
make deploy-web

# Python Microservices 
make deploy-api
make deploy-worker
```
