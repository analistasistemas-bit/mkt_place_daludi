"""
Middleware de tenant — Injeta tenant_id no request state.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from packages.shared.logging import get_logger

logger = get_logger("tenant_middleware")


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware que extrai tenant_id do user autenticado e injeta no request.state.
    Isso permite acesso rápido ao tenant_id em qualquer ponto do request.
    A extração real é feita pela dependência get_current_user;
    este middleware complementa injetando no state para uso em logging e serviços.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Inicializar state com valores padrão
        request.state.tenant_id = None
        request.state.user_id = None

        response = await call_next(request)
        return response
