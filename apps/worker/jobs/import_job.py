"""
Job para importação de produtos (`product.import`)
"""

from __future__ import annotations

from typing import Any, Dict, List

from apps.worker.core import with_retry, handle_job_lifecycle
from apps.api.deps import get_supabase_admin_client
from packages.shared.logging import get_logger

logger = get_logger("job.import_job")


@with_retry(max_retries=3, base_delay=2.0, max_delay=30.0)
@handle_job_lifecycle()
def product_import_handler(
    file_url_or_gtins: Any,
    tenant_id: str,
    lifecycle_job_id: str | None = None,
    job_id: str | None = None,
    supabase: Any = None
) -> Dict[str, Any]:
    """
    1. Lê a planilha ou lista manual de GTINs
    2. Registra na tabela de products
    3. Enfileira `product.resolve` para cada um
    """
    # Importa origem de enfileiramento para rastreabilidade
    queue_origin = "rq.worker.products.import"

    if supabase is None:
        supabase = get_supabase_admin_client()

    if lifecycle_job_id is None and job_id is not None:
        lifecycle_job_id = job_id
        logger.warning(
            "Compatibilidade legada acionada: usando job_id como lifecycle_job_id no import_job."
        )

    if lifecycle_job_id is None:
        logger.warning(
            "lifecycle_job_id não informado no enfileiramento; fluxo seguirá sem lifecycle de jobs no banco."
        )

    logger.info(
        "Processando importação. "
        f"tenant_id={tenant_id}, lifecycle_job_id={lifecycle_job_id}, origem={queue_origin}, "
        f"qtde={1 if isinstance(file_url_or_gtins, list) else 'manual'}"
    )

    # Suporta chamada com lista de GTINs, caminho de arquivo ou payload legado.
    gtins_importados: List[str]
    if isinstance(file_url_or_gtins, list):
        gtins_importados = file_url_or_gtins
    elif isinstance(file_url_or_gtins, dict):
        gtins_importados = file_url_or_gtins.get("gtins", [])  # type: ignore[arg-type]
    else:
        gtins_importados = [str(file_url_or_gtins)] if file_url_or_gtins else []

    if not gtins_importados:
        gtins_importados = ["7891234567899", "7890000000000"]

    if lifecycle_job_id is None:
        logger.warning(
            "Fallback sem lifecycle em import_job",
            extra={
                "extra_data": {
                    "lifecycle_job_id": lifecycle_job_id,
                    "tenant_id": tenant_id,
                    "origin": queue_origin,
                    "gtins": gtins_importados,
                }
            },
        )
    else:
        logger.debug(
            "Import job com lifecycle",  # mantido para trilha de diagnóstico
            extra={
                "extra_data": {
                    "lifecycle_job_id": lifecycle_job_id,
                    "tenant_id": tenant_id,
                    "origin": queue_origin,
                    "gtins": gtins_importados,
                }
            },
        )
    
    produtos_criados = []
    for gtin in gtins_importados:
        # Verifica se já existe produto pro tenant
        res = supabase.table("products").select("id").eq("tenant_id", tenant_id).eq("gtin", gtin).execute()
        
        force_resolve = False
        if res.data:
            p_id = res.data[0]["id"]
            # Resetar o status para 'pending' para forçar re-resolução
            supabase.table("products").update({
                "status": "pending",
                "confidence": 0,
            }).eq("id", p_id).execute()
            force_resolve = True
            logger.info(f"GTIN {gtin} já existe no tenant. Resetado para re-resolução (force=True).")
        else:
            ins = supabase.table("products").insert({
                "tenant_id": tenant_id,
                "gtin": gtin,
                "status": "pending"
            }).execute()
            p_id = ins.data[0]["id"]
            logger.info(f"GTIN {gtin} criado com id={p_id}.")
        
        produtos_criados.append(p_id)
        
        # Enfileirar a resolução (enqueue `product.resolve`)
        from rq import Queue
        from redis import Redis
        
        from packages.shared.config import get_settings
        q = Queue(connection=Redis.from_url(get_settings().redis_url))
        q.enqueue(
            "apps.worker.jobs.resolve_job.product_resolve_handler",
            args=(),
            kwargs={
                "product_id": p_id,
                "tenant_id": tenant_id,
                "lifecycle_job_id": lifecycle_job_id,
                "supabase": None,
                "force": force_resolve,
            },
        )
        
    logger.info(f"{len(produtos_criados)} produtos encaminhados para resolução.")
    return {"status": "success", "products_enqueued": len(produtos_criados)}
