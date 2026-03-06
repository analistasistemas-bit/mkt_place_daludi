"""
Dependências FastAPI — Supabase client, autenticação e tenant.
"""

from __future__ import annotations

import uuid
from functools import lru_cache
from typing import Annotated, Any, Optional

from fastapi import Depends, HTTPException, Request, status
from jose import jwt
from supabase import Client, create_client

from packages.shared.config import Settings, get_settings


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
        
        # Validar JWT localmente usando o SUPABASE_JWT_SECRET
        if settings.supabase_jwt_secret:
            try:
                payload = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False} # Supabase usa aud: "authenticated"
                )
                user_id = payload.get("sub")
                email = payload.get("email")
                
                if not user_id:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token inválido: campo 'sub' ausente",
                    )
            except Exception as e:
                # Import logger if needed or use internal print for now if logger not in scope
                # but logger is usually in routers. I should check if logger is in deps.py
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Token inválido ou expirado (local): {str(e)}",
                )
        else:
            # Fallback para o modo antigo se o secret não estiver configurado
            supabase = get_supabase_admin_client()
            user_response = supabase.auth.get_user(token)
            if not user_response or not user_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token inválido ou expirado",
                )
            user_id = str(user_response.user.id)
            email = user_response.user.email

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
