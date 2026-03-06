"""
Dependências FastAPI — Supabase client, autenticação e tenant.
"""

from __future__ import annotations

import time
import uuid
from functools import lru_cache
from typing import Annotated, Any, Optional

from fastapi import Depends, HTTPException, Request, status
import httpx
from supabase import Client, create_client
from jose import JWTError, jwt

from packages.shared.config import Settings, get_settings

_JWKS_CACHE: dict[str, Any] = {"keys": []}
_JWKS_CACHE_TS: float = 0.0
_JWKS_CACHE_TTL_SECONDS = 300.0


# ============================================================
# Supabase Clients
# ============================================================

@lru_cache()
def get_supabase_admin_client() -> Client:
    """Client Supabase com service_role_key (acesso admin, bypass RLS)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


@lru_cache()
def get_supabase_anon_client() -> Client:
    """Client Supabase com anon_key (respeita RLS)."""
    settings = get_settings()
    return create_client(settings.supabase_url, settings.supabase_anon_key)


# ============================================================
# JWT Validation
# ============================================================

async def _get_supabase_jwks(settings: Settings) -> dict[str, Any]:
    global _JWKS_CACHE, _JWKS_CACHE_TS

    now = time.time()
    if now - _JWKS_CACHE_TS < _JWKS_CACHE_TTL_SECONDS and _JWKS_CACHE.get("keys"):
        return _JWKS_CACHE

    jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(jwks_url)
        response.raise_for_status()
        data = response.json()

    keys = data.get("keys")
    if not isinstance(keys, list) or not keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro ao validar token: JWKS inválido",
        )

    _JWKS_CACHE = data
    _JWKS_CACHE_TS = now
    return _JWKS_CACHE


async def _decode_supabase_token(token: str, settings: Settings) -> dict[str, Any]:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erro ao validar token: {str(e)}",
        )

    alg = str(header.get("alg", "")).upper()
    if alg == "HS256":
        secret = (settings.supabase_jwt_secret or "").strip()
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="SUPABASE_JWT_SECRET não configurado",
            )
        try:
            return jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                audience="authenticated",
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Erro ao validar token: {str(e)}",
            )

    if alg == "RS256":
        jwks = await _get_supabase_jwks(settings)
        kid = header.get("kid")
        key = None
        if kid:
            key = next((k for k in jwks["keys"] if k.get("kid") == kid), None)
        if key is None and len(jwks["keys"]) == 1:
            key = jwks["keys"][0]
        if key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Erro ao validar token: kid não encontrado no JWKS",
            )
        try:
            return jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience="authenticated",
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Erro ao validar token: {str(e)}",
            )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=f"Erro ao validar token: algoritmo não suportado ({alg or 'desconhecido'})",
    )


# ============================================================
# Autenticação
# ============================================================

async def get_current_user(request: Request) -> dict[str, Any]:
    """
    Dependência que valida o JWT do Supabase Auth e retorna os dados do user.
    Extrai o token do header Authorization: Bearer <token>.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = auth_header.split(" ", 1)[1]

    try:
        settings = get_settings()
        payload = await _decode_supabase_token(token, settings)

        user_id = str(payload.get("sub", "")).strip()
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token inválido: sub não encontrado",
            )

        email = payload.get("email")
        if not isinstance(email, str):
            email = None

        # Buscar profile com tenant_id usando admin client
        supabase = get_supabase_admin_client()
        profile_response = (
            supabase.table("profiles")
            .select("*")
            .eq("id", str(user_id))
            .maybe_single()
            .execute()
        )

        tenant_id = None
        role = "member"
        if profile_response and profile_response.data:
            tenant_id = profile_response.data.get("tenant_id")
            role = profile_response.data.get("role", "member")

        return {
            "id": str(user_id),
            "email": email,
            "tenant_id": tenant_id,
            "role": role,
            "token": token,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Erro ao validar token: {str(e)}",
        )


async def get_tenant_id(
    current_user: Annotated[dict[str, Any], Depends(get_current_user)],
) -> uuid.UUID:
    """Dependência que extrai e valida o tenant_id do user autenticado."""
    tenant_id = current_user.get("tenant_id")
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário não está vinculado a nenhum tenant",
        )
    return uuid.UUID(str(tenant_id))


# ============================================================
# Type aliases para injeção de dependência
# ============================================================

CurrentUser = Annotated[dict[str, Any], Depends(get_current_user)]
TenantId = Annotated[uuid.UUID, Depends(get_tenant_id)]
SupabaseAdmin = Annotated[Client, Depends(get_supabase_admin_client)]
SupabaseAnon = Annotated[Client, Depends(get_supabase_anon_client)]
