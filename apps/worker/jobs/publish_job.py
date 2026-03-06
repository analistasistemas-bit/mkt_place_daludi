"""
Job para Publicação no ML (`listing.publish`)
"""

from typing import Any, Dict

from apps.worker.core import with_retry, handle_job_lifecycle
from apps.api.services.ml_service import get_ml_service
from packages.shared.logging import get_logger

logger = get_logger("job.publish_job")


@with_retry(max_retries=5, base_delay=5.0, max_delay=120.0) # retries mais longos pela rede com ML
@handle_job_lifecycle()
def listing_publish_handler(
    listing_id: str,
    job_id: str,
    tenant_id: str,
    supabase: Any
) -> Dict[str, Any]:
    """
    1. Verifica status no BD
    2. Envia para ml_service.publish_listing()
    3. Atualiza banco como `published` se ok.
    """
    logger.info(f"Publicando listing {listing_id}")
    
    res = supabase.table("listings").select("*").eq("id", listing_id).eq("tenant_id", tenant_id).execute()
    if not res.data:
        raise ValueError(f"Listing {listing_id} não encontrado.")
    
    listing = res.data[0]
    
    if listing.get("status") == "published":
        logger.info(f"Listing {listing_id} já publicado. Pulando (Idempotente).")
        return {"status": "skipped", "reason": "already_published"}
    
    if listing.get("status") != "ready":
        raise ValueError(f"Listing em status incorreto para publicação: {listing.get('status')}")
    
    ml_service = get_ml_service()
    
    import asyncio
    # mock token do tenant (ex: em tabela integrations)
    mock_token = "TEST_TOKEN_123" 
    
    # formatar os attributes corretamente de dict->list de obj
    attrs_ml = [
        {"id": k, "value_name": v} for k, v in listing.get("attributes", {}).items()
    ]
    
    # Asynchronous publish_listing from stub
    publish_result = asyncio.run(ml_service.publish_listing(
        title=listing.get("title", ""),
        price=listing.get("price", 0.0),
        currency_id=listing.get("currency", "BRL"),
        available_quantity=99,
        category_id=listing.get("category_id", "MLB1234"),
        attributes=attrs_ml,
        pictures=listing.get("images", []),
        access_token=mock_token
    ))
    
    if not publish_result or not publish_result.get("id"):
        raise Exception("O ML Service não retornou o ID da publicação (Meli ID).")
        
    ml_id = publish_result.get("id")
    
    # Salvar de volta
    supabase.table("listings").update({
        "status": "published",
        "metadata": {"ml_id": ml_id, "ml_permalink": publish_result.get("permalink", "")}
    }).eq("id", listing_id).execute()
    
    logger.info(f"Publicação completa do listing {listing_id} (ML_ID={ml_id})")
    
    return {"status": "success", "ml_id": ml_id}
