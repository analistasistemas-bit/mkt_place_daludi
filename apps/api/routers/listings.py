"""
Router de listings — Listagem de anúncios e publicação no Mercado Livre.
"""

from __future__ import annotations

import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from apps.api.deps import CurrentUser, SupabaseAdmin, TenantId
from packages.shared.logging import get_logger
from packages.shared.schemas import ListingStatus

router = APIRouter(prefix="/listings", tags=["Listings"])
logger = get_logger("router.listings")


# ============================================================
# GET /listings — Listar anúncios do tenant
# ============================================================

@router.get("")
async def list_listings(
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ListingStatus] = Query(default=None, alias="status"),
):
    """Lista anúncios do tenant com paginação e filtros."""
    query = (
        supabase.table("listings")
        .select("*, products(gtin, title, brand)", count="exact")
        .eq("tenant_id", str(tenant_id))
        .order("created_at", desc=True)
    )

    if status_filter:
        query = query.eq("status", status_filter.value)

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
# GET /listings/{id} — Detalhe do anúncio
# ============================================================

@router.get("/{listing_id}")
async def get_listing(
    listing_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
):
    """Retorna detalhes de um anúncio com versões."""
    listing_result = (
        supabase.table("listings")
        .select("*, products(gtin, title, brand, category)")
        .eq("id", str(listing_id))
        .eq("tenant_id", str(tenant_id))
        .maybe_single()
        .execute()
    )

    if not listing_result or not listing_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anúncio não encontrado",
        )

    listing = listing_result.data

    # Buscar versões
    versions_result = (
        supabase.table("listing_versions")
        .select("*")
        .eq("listing_id", str(listing_id))
        .eq("tenant_id", str(tenant_id))
        .order("version", desc=True)
        .execute()
    )

    return {
        **listing,
        "versions": versions_result.data or [],
    }


# ============================================================
# POST /listings/{id}/publish — Publicar anúncio no ML
# ============================================================

@router.post("/{listing_id}/publish", status_code=status.HTTP_202_ACCEPTED)
async def publish_listing(
    listing_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
):
    """
    Enfileira job para publicar anúncio no Mercado Livre.
    O anúncio deve estar com status 'approved' para ser publicado.
    """
    # Verificar se o listing existe e está aprovado
    listing_result = (
        supabase.table("listings")
        .select("id, status, compliance_status")
        .eq("id", str(listing_id))
        .eq("tenant_id", str(tenant_id))
        .maybe_single()
        .execute()
    )

    if not listing_result or not listing_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anúncio não encontrado",
        )

    listing = listing_result.data

    if listing["status"] not in ("approved", "ready"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Anúncio com status '{listing['status']}' não pode ser publicado. "
                   f"Status deve ser 'approved' ou 'ready'.",
        )

    # Criar job de publicação
    idempotency_key = f"publish-{listing_id}-{uuid.uuid4().hex[:8]}"

    job_result = (
        supabase.table("jobs")
        .insert({
            "tenant_id": str(tenant_id),
            "job_type": "listing.publish",
            "status": "pending",
            "payload": {
                "listing_id": str(listing_id),
                "tenant_id": str(tenant_id),
                "user_id": current_user["id"],
            },
            "idempotency_key": idempotency_key,
        })
        .execute()
    )

    if not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar job de publicação",
        )

    job = job_result.data[0]

    # Criar evento
    supabase.table("job_events").insert({
        "tenant_id": str(tenant_id),
        "job_id": job["id"],
        "event_type": "created",
        "message": f"Job de publicação criado para listing {listing_id}",
    }).execute()

    logger.info(
        "Job de publicação criado",
        extra={"extra_data": {
            "job_id": job["id"],
            "listing_id": str(listing_id),
            "tenant_id": str(tenant_id),
        }},
    )

    # TODO: Enfileirar job no RQ (Fase 4)
    # queue.enqueue(process_listing_publish, job["id"])

    return {
        "message": "Publicação iniciada",
        "job_id": job["id"],
        "listing_id": str(listing_id),
        "status": "pending",
    }


# ============================================================
# POST /listings/{id}/approve — Aprovar anúncio (revisão humana)
# ============================================================

@router.post("/{listing_id}/approve")
async def approve_listing(
    listing_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
):
    """Aprova um anúncio após revisão humana."""
    listing_result = (
        supabase.table("listings")
        .select("id, status, version")
        .eq("id", str(listing_id))
        .eq("tenant_id", str(tenant_id))
        .maybe_single()
        .execute()
    )

    if not listing_result or not listing_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Anúncio não encontrado",
        )

    listing = listing_result.data

    if listing["status"] not in ("draft", "ready", "pending_review"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Anúncio com status '{listing['status']}' não pode ser aprovado",
        )

    # Atualizar status
    supabase.table("listings").update({
        "status": "approved",
    }).eq("id", str(listing_id)).eq("tenant_id", str(tenant_id)).execute()

    # Audit log
    supabase.table("audit_logs").insert({
        "tenant_id": str(tenant_id),
        "user_id": current_user["id"],
        "action": "listing.approved",
        "resource_type": "listing",
        "resource_id": str(listing_id),
    }).execute()

    logger.info(
        "Anúncio aprovado",
        extra={"extra_data": {
            "listing_id": str(listing_id),
            "tenant_id": str(tenant_id),
            "approved_by": current_user["id"],
        }},
    )

    return {"message": "Anúncio aprovado", "listing_id": str(listing_id), "status": "approved"}
