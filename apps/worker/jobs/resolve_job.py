"""
Job para resolução e normalização de Produto (`product.resolve`)
"""

from typing import Any, Dict

from apps.worker.core import with_retry, handle_job_lifecycle
from apps.api.deps import get_supabase_admin_client
from apps.api.services.normalizer import get_normalizer
from apps.api.services.identity_resolver import get_identity_resolver
from packages.shared.logging import get_logger

logger = get_logger("job.resolve_job")


@with_retry(max_retries=3)
@handle_job_lifecycle()
def product_resolve_handler(
    product_id: str,
    job_id: str,
    tenant_id: str,
    supabase: Any = None
) -> Dict[str, Any]:
    """
    Executa a etapa 1 do Pipeline GTIN:
    Busca no Supabase -> GS1 -> Normaliza -> Calcula Confiança.
    """
    logger.info(f"Resolvendo produto {product_id}. tenant_id={tenant_id}")

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
    
    # 2. Mock de dados GS1 se precisar enriquecer product_data original
    normalized = normalizer.normalize_product(product_data)
    
    ident = resolver.resolve_confidence(normalized, sources=[{"source_type": "stub"}])
    status = ident["status"]
    
    # 3. Salvar volta no supabase
    supabase.table("products").update({
        "status": status,
        "confidence": ident["confidence"],
        "attributes": normalized.get("attributes", {})
    }).eq("id", product_id).execute()
    
    # 4. Enfileirar próxima etapa se ok
    if resolver.should_proceed_to_listing(ident):
        from rq import Queue
        from redis import Redis
        import os
        q = Queue(connection=Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")))
        q.enqueue(
            "apps.worker.jobs.generate_job.listing_generate_handler",
            product_id,
            job_id=job_id,
            tenant_id=tenant_id,
            supabase=None
        )
    else:
        logger.warning(f"Produto {product_id} bloqueado. Não segue para listing.generate.")
    
    return {"status": "success", "confidence": ident["confidence"], "identity_status": status}
