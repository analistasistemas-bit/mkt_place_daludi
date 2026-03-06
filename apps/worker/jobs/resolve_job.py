"""
Job para resolução e normalização de Produto (`product.resolve`)
"""

from __future__ import annotations

from typing import Any, Dict

from apps.worker.core import with_retry, handle_job_lifecycle
from apps.api.deps import get_supabase_admin_client
from apps.api.services.normalizer import get_normalizer
from apps.api.services.identity_resolver import get_identity_resolver
from apps.api.services.product_fetch_service import get_product_fetch_service
from packages.shared.logging import get_logger

logger = get_logger("job.resolve_job")

REPLACEABLE_TITLE_VALUES = {
    "",
    "Produto Sem Título Gerado",
}


def _should_replace_field(field: str, current_value: Any, new_value: Any) -> bool:
    if new_value in (None, "", [], {}):
        return False

    if field == "title":
        return (current_value or "").strip() in REPLACEABLE_TITLE_VALUES

    if field in {"brand", "category", "description"}:
        return not current_value

    if field in {"attributes", "images"}:
        return not current_value

    return not current_value


@with_retry(max_retries=3)
@handle_job_lifecycle()
def product_resolve_handler(
    product_id: str,
    tenant_id: str,
    lifecycle_job_id: str | None = None,
    job_id: str | None = None,
    supabase: Any = None
) -> Dict[str, Any]:
    """
    Executa a etapa 1 do Pipeline GTIN:
    Busca no Supabase -> GS1 -> Normaliza -> Calcula Confiança.
    """
    logger.info(f"Resolvendo produto {product_id}. tenant_id={tenant_id}")
    if lifecycle_job_id is None and job_id is not None:
        lifecycle_job_id = job_id
        logger.warning(
            f"Compatibilidade legada acionada: usando job_id como lifecycle_job_id no resolve_job para product_id={product_id}."
        )

    if not lifecycle_job_id:
        logger.warning(
            f"product_resolve_handler iniciado sem lifecycle_job_id para product_id={product_id}. tenant_id={tenant_id}"
        )

    if supabase is None:
        supabase = get_supabase_admin_client()
    
    res = supabase.table("products").select("*").eq("id", product_id).eq("tenant_id", tenant_id).execute()
    if not res.data:
        raise ValueError(f"Produto {product_id} não encontrado.")
    
    product_data = res.data[0]
    
    # Se houver status que indica processado, pode ser idempotente.
    if product_data.get("status") in ["resolved", "needs_review", "blocked"]:
        logger.info(f"Produto {product_id} já resolvido antes. Pulando.")
        return {"status": "skipped", "reason": "already_resolved"}
    
    # 1. Obter normalizer e identity
    normalizer = get_normalizer()
    resolver = get_identity_resolver()
    fetch_service = get_product_fetch_service()
    
    # 2. Buscar dados reais (Cascading Resolver)
    gtin = product_data.get("gtin")
    sources = []
    
    if gtin:
        logger.info(f"Buscando dados reais via cascading resolver para GTIN {gtin}...")
        import asyncio
        lookup_result = asyncio.run(fetch_service.lookup_by_gtin(gtin))
        sources.append({"source_type": lookup_result.source})
        
        if lookup_result.found:
            for k, v in lookup_result.data.items():
                if _should_replace_field(k, product_data.get(k), v):
                    product_data[k] = v
    else:
        sources.append({"source_type": "manual"})
    
    # 3. Normalizar
    normalized = normalizer.normalize_product(product_data)
    
    # 4. Calcular confidence
    ident = resolver.resolve_confidence(normalized, sources=sources)
    status = ident["status"]
    
    # 3. Salvar volta no supabase
    update_data = {
        "status": status,
        "confidence": ident["confidence"],
    }
    
    # Salvar os campos que foram enriquecidos pelo fetch service
    for field in ["title", "brand", "category", "description", "images", "attributes"]:
        if normalized.get(field):
            update_data[field] = normalized[field]
            
    supabase.table("products").update(update_data).eq("id", product_id).execute()
    
    # 4. Enfileirar próxima etapa se ok
    if resolver.should_proceed_to_listing(ident):
        from rq import Queue
        from redis import Redis
        import os
        q = Queue(connection=Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")))
        q.enqueue(
            "apps.worker.jobs.generate_job.listing_generate_handler",
            args=(),
            kwargs={
                "product_id": product_id,
                "tenant_id": tenant_id,
                "lifecycle_job_id": lifecycle_job_id,
                "supabase": None,
            },
        )
    else:
        logger.warning(f"Produto {product_id} bloqueado. Não segue para listing.generate.")
    
    return {"status": "success", "confidence": ident["confidence"], "identity_status": status}
