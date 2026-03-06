# Tarefas — Fase 2 (API Core)

## Planejamento
- [x] Criar plano de implementação da Fase 2
- [x] Aprovação do plano

## Execução — Supabase Client
- [x] Criar [apps/api/deps.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/deps.py) (Supabase client + dependências FastAPI)

## Execução — Middleware
- [x] Criar [apps/api/middleware/auth.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/middleware/auth.py) (JWT + Supabase Auth)
- [x] Criar [apps/api/middleware/tenant.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/middleware/tenant.py) (tenant isolation)
- [x] Criar [apps/api/middleware/rate_limit.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/middleware/rate_limit.py) (rate limit básico)

## Execução — Routers
- [x] Criar [apps/api/routers/auth.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/auth.py) (POST /auth/login, /register, /refresh)
- [x] Criar [apps/api/routers/products.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/products.py) (POST /products/import, GET /products, GET /products/{id})
- [x] Criar [apps/api/routers/jobs.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/jobs.py) (GET /jobs, GET /jobs/{id})
- [x] Criar [apps/api/routers/listings.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/listings.py) (GET /listings, POST /listings/{id}/publish, /approve)
- [x] Criar [apps/api/routers/discovery.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/routers/discovery.py) (GET /discovery/opportunities — stub)

## Execução — App Principal
- [x] Criar [apps/api/main.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/main.py) (FastAPI app + routers + middleware + CORS)
- [x] Criar [apps/api/Dockerfile](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/api/Dockerfile)
- [x] Criar [apps/worker/Dockerfile](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/apps/worker/Dockerfile)

## Verificação
- [x] ✅ Todos os módulos importam sem erro
- [x] ✅ 19 rotas registradas na FastAPI
- [x] ✅ Corrigido MRO e type hints para Python 3.9
