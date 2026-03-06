"""
Middleware de rate limit — Limite básico por IP (in-memory).
"""

from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from packages.shared.logging import get_logger

logger = get_logger("rate_limit_middleware")


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limit básico por IP usando contagem em memória.
    Limite padrão: 100 requests por minuto por IP.
    Em produção, trocar por Redis-based rate limiting.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()

        # Limpar requests antigos
        self._requests[client_ip] = [
            t for t in self._requests[client_ip]
            if now - t < self.window_seconds
        ]

        # Verificar limite
        if len(self._requests[client_ip]) >= self.max_requests:
            logger.warning(
                "Rate limit excedido",
                extra={"extra_data": {"ip": client_ip, "count": len(self._requests[client_ip])}},
            )
            return Response(
                content='{"detail":"Limite de requisições excedido. Tente novamente em breve."}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": str(self.window_seconds)},
            )

        # Registrar request
        self._requests[client_ip].append(now)

        response = await call_next(request)

        # Adicionar headers de rate limit
        remaining = self.max_requests - len(self._requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))

        return response
