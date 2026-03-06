# Tarefas — Fase 1 (Base)

## Brainstorming
- [x] Ler todos os arquivos do projeto
- [x] Verificar estado do Supabase
- [x] Perguntas de brainstorming → decisões confirmadas

## Planejamento
- [x] Criar plano de implementação detalhado
- [x] Aprovação do plano pelo usuário

## Execução — Estrutura do Monorepo
- [x] Criar diretórios (apps/api, apps/worker, apps/web, packages/shared, supabase, docs)
- [x] Criar arquivos base (__init__.py, .gitkeep)

## Execução — Banco de Dados
- [x] Criar [supabase/schema.sql](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/supabase/schema.sql) (15 tabelas + pgvector)
- [x] Criar [supabase/rls.sql](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/supabase/rls.sql) (policies por tenant_id)
- [x] Criar [supabase/seeds.sql](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/supabase/seeds.sql) (tenant + templates)
- [x] Aplicar schema + RLS + seeds no Supabase

## Execução — Schemas Pydantic
- [x] Criar [packages/shared/__init__.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/packages/shared/__init__.py)
- [x] Criar [packages/shared/schemas.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/packages/shared/schemas.py) (contratos Pydantic v2)
- [x] Criar [packages/shared/config.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/packages/shared/config.py) (pydantic-settings)
- [x] Criar [packages/shared/logging.py](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/packages/shared/logging.py) (logging estruturado JSON)

## Execução — Infra e Tooling
- [x] Criar [docker-compose.yml](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/docker-compose.yml) (API + Worker + Redis)
- [x] Criar [.env.example](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/.env.example)
- [x] Criar [Makefile](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/Makefile)
- [x] Criar [README.md](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/README.md) base
- [x] Criar [requirements.txt](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/requirements.txt) + [requirements-dev.txt](file:///Users/diego/Desktop/IA/mktplace%20daludi%20full/requirements-dev.txt)

## Verificação
- [x] ✅ 15/15 tabelas criadas no Supabase
- [x] ✅ RLS habilitado em todas as tabelas
- [x] ✅ Seeds inseridos (1 tenant, 3 templates)
- [x] ✅ Estrutura de diretórios completa
