"""
Job para geração de anúncio (`listing.generate`)
"""

from __future__ import annotations

from typing import Any, Dict

from apps.worker.core import with_retry, handle_job_lifecycle
from apps.api.deps import get_supabase_admin_client
from apps.api.services.pipeline import get_pipeline
from packages.shared.logging import get_logger

logger = get_logger("job.generate_job")


@with_retry(max_retries=3)
@handle_job_lifecycle()
def listing_generate_handler(
    product_id: str,
    tenant_id: str,
    lifecycle_job_id: str | None = None,
    job_id: str | None = None,
    supabase: Any = None
) -> Dict[str, Any]:
    """
    Executa Etapas 2-5 do Pipeline (Template, Pricing, Vector e AI).
    - Exige que o DB tenha o produto na tabela products.
    - Salva na tabela listings.
    """
    logger.info(f"Gerando listing do produto {product_id}")
    if lifecycle_job_id is None and job_id is not None:
        lifecycle_job_id = job_id
        logger.warning(
            f"Compatibilidade legada acionada: usando job_id como lifecycle_job_id no generate_job para product_id={product_id}."
        )

    if not lifecycle_job_id:
        logger.warning(
            f"listing_generate_handler iniciado sem lifecycle_job_id para product_id={product_id}. tenant_id={tenant_id}"
        )

    if supabase is None:
        supabase = get_supabase_admin_client()
    
    res = supabase.table("products").select("*").eq("id", product_id).eq("tenant_id", tenant_id).execute()
    if not res.data:
        raise ValueError(f"Produto {product_id} não encontrado.")
    
    product_data = res.data[0]
    
    # Idempotência: Checa se já não gerou o listing
    # usando idempotency_key preestabelecida na tabela listings
    l_res = supabase.table("listings").select("id").eq("product_id", product_id).eq("status", "ready").execute()
    if l_res.data:
        logger.info(f"Listing para prod {product_id} já gerado (idempotência).")
        return {"status": "skipped", "reason": "already_generated"}
    
    # Obtém pipeline orquestrador completo
    pipeline = get_pipeline()
    
    # Configura um eventloop (RQ roda Síncrono, pipeline.execute é async)
    import asyncio
    
    # Obter os tenant_settings para margem etc. (mock no momento)
    t_settings = {"default_margin": 0.3}

    result = asyncio.run(pipeline.execute(
        product_data=product_data,
        tenant_id=tenant_id,
        sources=[{"source_type": "stub"}],
        tenant_settings=t_settings
    ))
    
    if not result.success:
        raise RuntimeError(f"Erro na pipeline em stage {result.stage}: {result.error}")
    
    generated_listing = result.listing
    assert generated_listing is not None

    # Como pipeline não inseriu no DB e sim retornou o objeto gerado, nós o inserimos/atualizamos
    ins = supabase.table("listings").insert(generated_listing).execute()
    listing_id = ins.data[0]["id"]
    
    # Se gerou ok e está ready, enfilera o publish.
    if generated_listing.get("status") == "ready":
        from rq import Queue
        from redis import Redis
        import os
        q = Queue(connection=Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")))
        q.enqueue(
            "apps.worker.jobs.publish_job.listing_publish_handler",
            args=(),
            kwargs={
                "listing_id": listing_id,
                "tenant_id": tenant_id,
                "lifecycle_job_id": lifecycle_job_id,
                "supabase": None,
            },
        )
    else:
         logger.warning(f"Listing {listing_id} não enfileirado para publish (status={generated_listing.get('status')})")

    return {"status": "success", "listing_id": listing_id}
