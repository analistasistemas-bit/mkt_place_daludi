"""
Router de produtos — Import, listagem e detalhes.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, File, HTTPException, Query, UploadFile, status
from redis import Redis
from rq import Queue

from apps.api.deps import CurrentUser, SupabaseAdmin, TenantId
from packages.shared.config import get_settings
from packages.shared.logging import get_logger
from packages.shared.schemas import PaginatedResponse, ProductStatus

router = APIRouter(prefix="/products", tags=["Produtos"])
logger = get_logger("router.products")


# ============================================================
# POST /products/import — Importar produtos
# ============================================================

from pydantic import BaseModel

class ImportProductsRequest(BaseModel):
    gtins: Optional[list[str]] = None

@router.post("/import", status_code=status.HTTP_202_ACCEPTED)
async def import_products(
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
    request: ImportProductsRequest,
):
    """
    Importa produtos via lista de GTINs (MVP em JSON).
    Cria um job assíncrono de importação.
    """
    gtins = request.gtins
    
    if not gtins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Forneça uma lista de GTINs",
        )

    # Montar payload do job
    payload: dict[str, Any] = {
        "tenant_id": str(tenant_id),
        "user_id": current_user["id"],
    }

    if gtins:
        payload["gtins"] = gtins
        payload["source"] = "manual"

    # Criar job de importação
    idempotency_key = f"import-{tenant_id}-{uuid.uuid4().hex[:8]}"

    job_result = (
        supabase.table("jobs")
        .insert({
            "tenant_id": str(tenant_id),
            "job_type": "product.import",
            "status": "pending",
            "payload": payload,
            "idempotency_key": idempotency_key,
        })
        .execute()
    )

    if not job_result.data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao criar job de importação",
        )

    job = job_result.data[0]

    # Criar evento de job
    supabase.table("job_events").insert({
        "tenant_id": str(tenant_id),
        "job_id": job["id"],
        "event_type": "created",
        "message": f"Job de importação criado com {len(gtins) if gtins else 1} item(ns)",
    }).execute()

    logger.info(
        "Job de importação criado",
        extra={"extra_data": {
            "job_id": job["id"],
            "tenant_id": str(tenant_id),
            "source": payload.get("source"),
        }},
    )

    # Enfileirar processamento assíncrono no RQ
    settings = get_settings()
    queue = Queue(connection=Redis.from_url(settings.redis_url))
    queue.enqueue(
        "apps.worker.jobs.import_job.product_import_handler",
        gtins,
        job_id=job["id"],
        tenant_id=str(tenant_id),
        supabase=None,
    )

    return {
        "message": "Importação iniciada",
        "job_id": job["id"],
        "status": "pending",
    }


# ============================================================
# GET /products — Listar produtos do tenant
# ============================================================

@router.get("", response_model=PaginatedResponse)
async def list_products(
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[ProductStatus] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None),
):
    """Lista produtos do tenant com paginação e filtros."""
    query = (
        supabase.table("products")
        .select("*", count="exact")
        .eq("tenant_id", str(tenant_id))
        .order("created_at", desc=True)
    )

    if status_filter:
        query = query.eq("status", status_filter.value)

    if search:
        query = query.or_(f"gtin.ilike.%{search}%,title.ilike.%{search}%,brand.ilike.%{search}%")

    # Paginação
    offset = (page - 1) * per_page
    query = query.range(offset, offset + per_page - 1)

    result = query.execute()

    total = result.count if result.count is not None else 0
    pages = (total + per_page - 1) // per_page if total > 0 else 0

    return PaginatedResponse(
        items=result.data or [],
        total=total,
        page=page,
        per_page=per_page,
        pages=pages,
    )


# ============================================================
# GET /products/{id} — Detalhe do produto
# ============================================================

@router.get("/{product_id}")
async def get_product(
    product_id: uuid.UUID,
    current_user: CurrentUser,
    tenant_id: TenantId,
    supabase: SupabaseAdmin,
):
    """Retorna detalhes de um produto específico com suas fontes e evidências."""
    # Buscar produto
    product_result = (
        supabase.table("products")
        .select("*")
        .eq("id", str(product_id))
        .eq("tenant_id", str(tenant_id))
        .maybe_single()
        .execute()
    )

    if not product_result or not product_result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Produto não encontrado",
        )

    product = product_result.data

    # Buscar fontes
    sources_result = (
        supabase.table("product_sources")
        .select("*")
        .eq("product_id", str(product_id))
        .eq("tenant_id", str(tenant_id))
        .execute()
    )

    # Buscar evidências
    evidence_result = (
        supabase.table("product_evidence")
        .select("*")
        .eq("product_id", str(product_id))
        .eq("tenant_id", str(tenant_id))
        .execute()
    )

    return {
        **product,
        "sources": sources_result.data or [],
        "evidence": evidence_result.data or [],
    }
