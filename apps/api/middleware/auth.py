"""
Middleware de autenticação — Valida JWT Supabase em todas as rotas protegidas.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from packages.shared.logging import get_logger

logger = get_logger("auth_middleware")

# Rotas que não precisam de autenticação
PUBLIC_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/auth/login",
    "/auth/register",
    "/auth/refresh",
}


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que verifica se requests possuem token JWT válido.
    Rotas públicas são liberadas sem autenticação.
    A validação real do token é feita na dependência get_current_user.
    Este middleware apenas garante a presença do header.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        path = request.url.path

        # Liberar rotas públicas
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/redoc"):
            return await call_next(request)

        # Verificar presença do header Authorization
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return Response(
                content='{"detail":"Token de autenticação não fornecido"}',
                status_code=401,
                media_type="application/json",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
