"""
Job de Discovery Scan (`discovery.scan`). (Stub MVP)
"""

from typing import Any, Dict

from apps.worker.core import with_retry, handle_job_lifecycle
from packages.shared.logging import get_logger

logger = get_logger("job.discovery_job")


@with_retry(max_retries=1)
@handle_job_lifecycle()
def discovery_scan_handler(
    job_id: str,
    tenant_id: str,
    supabase: Any
) -> Dict[str, Any]:
    """
    Executa busca de oportunidades e atualiza a tabela `opportunities`.
    STUB no MVP.
    """
    logger.info("Executando stub de discovery.scan")
    
    # Criar 2 oportunidades pro tenant e inserir na tabela (stubbing)
    opps = [
         {"tenant_id": tenant_id, "gtin": "7891112223334", "score": 88, "status": "new"},
         {"tenant_id": tenant_id, "gtin": "7899998887776", "score": 92, "status": "new"}
    ]
    
    try:
        supabase.table("opportunities").insert(opps).execute()
        return {"status": "success", "opportunities_found": 2}
    except Exception as e:
         # Provavelmente constraint violada e a tabela opp não existe no seed basico, então suprimimos.
         # De fato existe: docs falam tabela opportunities stub
         logger.warning("Falha inserindo oportunidades stub: " + str(e))
         return {"status": "failed_stub", "error": str(e)}
