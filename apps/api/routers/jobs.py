"""
Router de jobs — Consulta de status e eventos de jobs.
"""

from __future__ import annotations

from typing import Any, Optional

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from apps.api.deps import CurrentUser, SupabaseAdmin, TenantId
from packages.shared.logging import get_logger

router = APIRouter(prefix="/jobs", tags=["Jobs"])
logger = get_logger("router.jobs")


def _ensure_admin_role(current_user: dict[str, Any]) -> None:
    role = current_user.get("role")
    if role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem excluir jobs em lote.",
        )


# ============================================================
# GET /jobs/{id} — Detalhe do job com eventos
# ============================================================

@router.get("/{job_id}")
async def get_job(
    job_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
):
    """Retorna detalhes de um job com seus eventos."""
    # Buscar job
    job_result = (
        supabase.table("jobs")
        .select("*")
        .eq("id", str(job_id))
        .eq("tenant_id", str(tenant_id))
        .maybe_single()
        .execute()
    )

    if not job_result or not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job não encontrado",
        )

    job = job_result.data

    # Buscar eventos do job
    events_result = (
        supabase.table("job_events")
        .select("*")
        .eq("job_id", str(job_id))
        .eq("tenant_id", str(tenant_id))
        .order("created_at", desc=False)
        .execute()
    )

    return {
        **job,
        "events": events_result.data or [],
    }


# ============================================================
# GET /jobs — Listar jobs do tenant
# ============================================================

@router.get("")
async def list_jobs(
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    job_type: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
):
    """Lista jobs do tenant com paginação e filtros."""
    query = (
        supabase.table("jobs")
        .select("*", count="exact")
        .eq("tenant_id", str(tenant_id))
        .order("created_at", desc=True)
    )

    if job_type:
        query = query.eq("job_type", job_type)

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
    }


# ============================================================
# DELETE /jobs/pending — Remover jobs pendentes do tenant (admin)
# ============================================================


@router.delete("/pending")
async def delete_pending_jobs(
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
):
    """Remove todos os jobs com status `pending` do tenant atual."""
    _ensure_admin_role(current_user)

    pending_jobs = (
        supabase.table("jobs")
        .select("id")
        .eq("tenant_id", str(tenant_id))
        .eq("status", "pending")
        .execute()
    )

    job_ids = [job["id"] for job in (pending_jobs.data or [])]

    if not job_ids:
        return {"deleted_jobs": 0, "message": "Nenhum job pendente para excluir."}

    # Limpar eventos primeiro para evitar órfãos e manter histórico consistente.
    supabase.table("job_events").delete().in_("job_id", job_ids).execute()
    supabase.table("jobs").delete().in_("id", job_ids).execute()

    logger.info(
        "Jobs pendentes removidos",
        extra={"extra_data": {"tenant_id": str(tenant_id), "count": len(job_ids)}},
    )

    return {
        "deleted_jobs": len(job_ids),
        "message": "Jobs pendentes removidos com sucesso.",
    }
