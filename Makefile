# ============================================================
# Marketplace SaaS — Makefile
# ============================================================

.PHONY: dev dev-api dev-worker migrate seed lint test \
        deploy-api deploy-worker deploy-web clean help

# ── Desenvolvimento Local ────────────────────────────────────

dev: ## Sobe API + Worker + Redis via Docker Compose
	docker compose up --build

dev-api: ## Roda apenas a API localmente (sem Docker)
	cd apps/api && uvicorn main:app --host 0.0.0.0 --port 8000 --reload

dev-worker: ## Roda apenas o Worker localmente (sem Docker)
	cd apps/worker && python -m rq worker --url $${REDIS_URL:-redis://localhost:6379/0} default high low

# ── Banco de Dados ───────────────────────────────────────────

migrate: ## Aplica schema.sql no Supabase
	@echo "📦 Aplicando schema no Supabase..."
	@echo "Use o dashboard Supabase ou o MCP para aplicar supabase/schema.sql"

seed: ## Roda seeds.sql no Supabase
	@echo "🌱 Inserindo seeds no Supabase..."
	@echo "Use o dashboard Supabase ou o MCP para aplicar supabase/seeds.sql"

# ── Qualidade de Código ──────────────────────────────────────

lint: ## Roda linters (ruff + black + mypy)
	ruff check apps/ packages/
	black --check apps/ packages/
	mypy apps/ packages/ --ignore-missing-imports

lint-fix: ## Corrige problemas de lint automaticamente
	ruff check apps/ packages/ --fix
	black apps/ packages/

test: ## Roda suite de testes
	pytest tests/ -v --tb=short

test-cov: ## Roda testes com cobertura
	pytest tests/ -v --tb=short --cov=apps --cov=packages --cov-report=term-missing

# ── Deploy ───────────────────────────────────────────────────

deploy-api: ## Deploy da API no Render
	@echo "🚀 Deploy API..."
	@echo "Configure o serviço no Render apontando para apps/api"
	@echo "Start command: uvicorn apps.api.main:app --host 0.0.0.0 --port $$PORT"

deploy-worker: ## Deploy do Worker no Render
	@echo "🚀 Deploy Worker..."
	@echo "Configure o serviço no Render apontando para apps/worker"
	@echo "Start command: python -m rq worker --url $$REDIS_URL default high low"

deploy-web: ## Deploy do Frontend na Vercel
	@echo "🚀 Deploy Web..."
	@echo "Configure o projeto na Vercel apontando para apps/web"

# ── Utilitários ──────────────────────────────────────────────

clean: ## Limpa arquivos temporários
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .mypy_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

install: ## Instala dependências Python
	pip install -r requirements.txt

install-dev: ## Instala dependências de desenvolvimento
	pip install -r requirements-dev.txt

help: ## Mostra esta ajuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help
