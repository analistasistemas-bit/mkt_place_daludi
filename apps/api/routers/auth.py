"""
Router de autenticação — Login via Supabase Auth.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr

from apps.api.deps import get_supabase_admin_client
from packages.shared.logging import get_logger

router = APIRouter(prefix="/auth", tags=["Autenticação"])
logger = get_logger("router.auth")


# ============================================================
# Request/Response Models
# ============================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    email: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    tenant_name: Optional[str] = None


class RefreshRequest(BaseModel):
    refresh_token: str


# ============================================================
# Endpoints
# ============================================================

@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest):
    """
    Autentica o usuário via Supabase Auth.
    Retorna access_token e refresh_token.
    """
    try:
        supabase = get_supabase_admin_client()
        response = supabase.auth.sign_in_with_password({
            "email": payload.email,
            "password": payload.password,
        })

        if not response or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Credenciais inválidas",
            )

        session = response.session
        user = response.user

        logger.info(
            "Login realizado com sucesso",
            extra={"extra_data": {"user_id": str(user.id), "email": user.email}},
        )

        return LoginResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or 3600,
            user_id=str(user.id),
            email=user.email or "",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
        )


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest):
    """
    Registra um novo usuário via Supabase Auth.
    Cria tenant e profile automaticamente.
    """
    try:
        supabase = get_supabase_admin_client()

        # 1. Criar usuário no Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": payload.email,
            "password": payload.password,
        })

        if not auth_response or not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Erro ao criar usuário",
            )

        user = auth_response.user
        tenant_name = payload.tenant_name or payload.email.split("@")[0]
        tenant_slug = tenant_name.lower().replace(" ", "-").replace("_", "-")

        # 2. Criar tenant
        tenant_result = (
            supabase.table("tenants")
            .insert({
                "name": tenant_name,
                "slug": tenant_slug,
                "plan": "free",
            })
            .execute()
        )

        if not tenant_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Erro ao criar tenant",
            )

        tenant_id = tenant_result.data[0]["id"]

        # 3. Criar profile
        supabase.table("profiles").insert({
            "id": str(user.id),
            "tenant_id": tenant_id,
            "full_name": payload.full_name,
            "role": "owner",
        }).execute()

        logger.info(
            "Usuário registrado com sucesso",
            extra={"extra_data": {
                "user_id": str(user.id),
                "tenant_id": tenant_id,
            }},
        )

        return {
            "message": "Usuário criado com sucesso",
            "user_id": str(user.id),
            "tenant_id": tenant_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro no registro: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Erro ao registrar: {str(e)}",
        )


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(payload: RefreshRequest):
    """Renova o access_token usando o refresh_token."""
    try:
        supabase = get_supabase_admin_client()
        response = supabase.auth.refresh_session(payload.refresh_token)

        if not response or not response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido",
            )

        session = response.session
        user = response.user

        return LoginResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            expires_in=session.expires_in or 3600,
            user_id=str(user.id) if user else "",
            email=user.email if user else "",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Erro ao renovar token",
        )
