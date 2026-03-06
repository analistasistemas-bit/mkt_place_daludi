"""
Router de discovery — Stub MVP para oportunidades.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Query

from apps.api.deps import CurrentUser, SupabaseAdmin, TenantId
from packages.shared.logging import get_logger

router = APIRouter(prefix="/discovery", tags=["Discovery (Stub)"])
logger = get_logger("router.discovery")


# ============================================================
# GET /discovery/opportunities — Listar oportunidades (stub)
# ============================================================

@router.get("/opportunities")
async def list_opportunities(
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[str] = Query(default=None, alias="status"),
):
    """
    Lista oportunidades de discovery.
    STUB MVP — retorna dados do banco sem lógica de análise.
    """
    query = (
        supabase.table("opportunities")
        .select("*", count="exact")
        .eq("tenant_id", str(tenant_id))
        .order("score", desc=True)
    )

    if status_filter:
        query = query.eq("status", status_filter)

    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = query.execute()

    total = result.count if result.count is not None else 0

    return {
        "items": result.data or [],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": (total + per_page - 1) // per_page if total > 0 else 0,
        "_stub": True,
        "_message": "Discovery é stub no MVP. Lógica de análise será implementada nas próximas fases.",
    }
