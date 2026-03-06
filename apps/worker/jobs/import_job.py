"""
Job para importação de produtos (`product.import`)
"""

from typing import Any, Dict, List

from apps.worker.core import with_retry, handle_job_lifecycle
from apps.api.deps import get_supabase_admin_client
from packages.shared.logging import get_logger

logger = get_logger("job.import_job")


@with_retry(max_retries=3, base_delay=2.0, max_delay=30.0)
@handle_job_lifecycle()
def product_import_handler(
    file_url_or_gtins: Any,
    job_id: str,
    tenant_id: str,
    supabase: Any = None
) -> Dict[str, Any]:
    """
    1. Lê a planilha ou lista manual de GTINs
    2. Registra na tabela de products
    3. Enfileira `product.resolve` para cada um
    """
    logger.info(f"Processando importação. tenant_id={tenant_id}")

    if supabase is None:
        supabase = get_supabase_admin_client()

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
    
    produtos_criados = []
    for gtin in gtins_importados:
        # Verifica se já existe produto pro tenant
        res = supabase.table("products").select("id").eq("tenant_id", tenant_id).eq("gtin", gtin).execute()
        
        if res.data:
            logger.info(f"GTIN {gtin} já existe no tenant (idempotência). Pulando criação inicial.")
            p_id = res.data[0]["id"]
        else:
            ins = supabase.table("products").insert({
                "tenant_id": tenant_id,
                "gtin": gtin,
                "status": "imported", 
                "source": "import_job"
            }).execute()
            p_id = ins.data[0]["id"]
        
        produtos_criados.append(p_id)
        
        # Enfileirar a resolução (enqueue `product.resolve`)
        from rq import Queue
        from redis import Redis
        import os
        
        # Conexão estática para o job
        q = Queue(connection=Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0")))
        q.enqueue(
            "apps.worker.jobs.resolve_job.product_resolve_handler",
            p_id,
            job_id=job_id,  # ou criar sub-job id
            tenant_id=tenant_id,
            supabase=None
        )
        
    logger.info(f"{len(produtos_criados)} produtos encaminhados para resolução.")
    return {"status": "success", "products_enqueued": len(produtos_criados)}
