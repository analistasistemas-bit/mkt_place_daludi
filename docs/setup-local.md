# Setup Deste Projeto Localmente

Siga estas instruções para configurar e rodar o Monorepo do **Daludi Marketplace** na sua máquina local (MacOS/Linux).

## 1. Pré-Requisitos
1. **Docker Desktop** ou `docker-compose` v2.
2. **Node.js** v20+ e Gerenciador de dependência `npm`.
3. **Python** 3.11+.
4. Conta gratuita no **Supabase**.
5. Instância do **Redis** (Local ou Upstash).

## 2. Supabase e Variáveis de Ambiente

1. Crie um projeto no Supabase (ex: `mkt_place_ia`).
2. Acesse _SQL Editor_ no painel e rode os arquivos na raiz em ordem:
   - `supabase/schema.sql`
   - `supabase/rls.sql`
   - `supabase/seeds.sql`
3. Vá em _Project Settings -> API_ para obter:
   - `URL` e `Anon Key` (Chaves públicas)
   - `Service Role Key` (Chave Root). CUIDADO.

Copie o `.env.example` para os `.env` das suas aplicações:
```bash
cp .env.example .env
cp apps/web/.env.example apps/web/.env.local
```

### Configurando o `.env` global para API + Worker
```env
# Banco & API Geral
SUPABASE_URL=https://<seu-projeto>.supabase.co
SUPABASE_ANON_KEY=eyJhbGci...
SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...
REDIS_URL=redis://localhost:6379/0

# Módulos Extra IA (Stubs ativados caso em branco)
LLM_API_KEY=sk-proj...
```

### Configurando `apps/web/.env.local`
```env
NEXT_PUBLIC_SUPABASE_URL=https://<seu-projeto>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGci...
API_URL=http://localhost:8000
```

## 3. Instalando as Dependências

### Node (App Web)
```bash
cd apps/web
npm install
```

### Python (API & Worker)
Recomendado usar `venv`:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
*(Nota: Certifique-se de configurar a variável `PYTHONPATH=.` ao rodar os scripts python sem ferramentas como Make/Docker).*

## 4. Rodando Localmente

A raiz do projeto provê um `docker-compose.yml` e um `Makefile` configurado para subir as infraestruturas que não podem ou não estão instanciadas no Cloud (Ex: Local Redis Server e Test API envs).

Abra três abas de terminal:

**Terminal 1 (Backend - FastAPI)**
```bash
make dev-api
# Inicia em http://localhost:8000
```

**Terminal 2 (Processos Async RQ - Worker)**
```bash
make dev-worker
```

**Terminal 3 (Frontend - Next.js)**
```bash
make dev-web
# Inicia em http://localhost:3000
```

Para simplificiar todos os processos, você também pode usar o Make puro (requer que você tenha seu servidor redis rodando na port 6379, ou execute o `docker-compose up -d redis` antes):
```bash
make dev
```

## 5. Testando
Acesse `http://localhost:3000`. Use os dados da Tabela `users` e `profiles` criados pela importação de sementes (Seeds) via script do seu painel Supabase Admin ou crie um usuário através da Aba _Authentication_ do seu painel Supabase com as premissas de RLS do seu Tenant (ex: TestTenantID).
