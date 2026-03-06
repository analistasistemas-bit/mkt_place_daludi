"""
Marketplace SaaS — FastAPI Application
Ponto de entrada principal da API.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from apps.api.middleware.auth import AuthMiddleware
from apps.api.middleware.rate_limit import RateLimitMiddleware
from apps.api.middleware.tenant import TenantMiddleware
from apps.api.routers import auth, discovery, jobs, listings, products
from packages.shared.config import get_settings
from packages.shared.logging import get_logger, setup_logging

logger = get_logger("api")


# ============================================================
# Lifespan Events
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup e shutdown events."""
    settings = get_settings()
    setup_logging(
        level="DEBUG" if settings.debug else "INFO",
        service_name="api",
    )
    logger.info(
        "API iniciando",
        extra={"extra_data": {"environment": settings.environment}},
    )
    yield
    logger.info("API encerrando")


# ============================================================
# App
# ============================================================

def create_app() -> FastAPI:
    """Factory para criar a instância FastAPI."""
    settings = get_settings()

    app = FastAPI(
        title="Marketplace SaaS API",
        description=(
            "API para geração e publicação automatizada de anúncios "
            "no Mercado Livre via GTIN. "
            "Pipeline: rules → templates → cache → vector reuse → AI."
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",  # Next.js dev
            "http://localhost:8000",  # API dev
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Custom Middleware (ordem importa: último adicionado = primeiro executado) ──
    app.add_middleware(TenantMiddleware)
    app.add_middleware(AuthMiddleware)
    app.add_middleware(RateLimitMiddleware, max_requests=100, window_seconds=60)

    # ── Routers ───────────────────────────────────────────────
    app.include_router(auth.router)
    app.include_router(products.router)
    app.include_router(jobs.router)
    app.include_router(listings.router)
    app.include_router(discovery.router)

    # ── Health Check ──────────────────────────────────────────
    @app.get("/", tags=["Health"])
    async def root():
        return {
            "service": "Marketplace SaaS API",
            "version": "0.1.0",
            "status": "healthy",
            "environment": settings.environment,
        }

    @app.get("/health", tags=["Health"])
    async def health():
        return {"status": "ok"}

    return app


# Instância global da app
app = create_app()
