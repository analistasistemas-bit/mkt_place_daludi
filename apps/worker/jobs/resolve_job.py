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
from apps.api.services.enrichment_service import get_enrichment_service
from packages.shared.logging import get_logger

logger = get_logger("job.resolve_job")

REPLACEABLE_TITLE_VALUES = {
    "",
    "Produto Sem Título Gerado",
}


def _should_replace_field(field: str, current_value: Any, new_value: Any) -> bool:
    """Decide se um campo deve ser substituído por um novo valor."""
    if new_value in (None, "", [], {}):
        return False

    if field == "title":
        # Aceitar novo valor se o atual é nulo, vazio, ou um placeholder genérico
        current_str = (current_value or "").strip()
        if not current_str or current_str in REPLACEABLE_TITLE_VALUES:
            return True
        # Também substituir se o título atual começa com "GTIN" ou "Gtin" (fallback)
        if current_str.lower().startswith("gtin ") or current_str.lower().startswith("gtin\u00a0"):
            return True
        return False

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
    supabase: Any = None,
    force: bool = False
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
    
    # Idempotência: só pular se já está 'resolved' com título válido E NÃO é force
    if not force:
        is_resolved = product_data.get("status") == "resolved"
        has_valid_title = (product_data.get("title") or "").strip() not in REPLACEABLE_TITLE_VALUES
        if has_valid_title:
            current_title = (product_data.get("title") or "").strip().lower()
            if current_title.startswith("gtin "):
                has_valid_title = False
        
        if is_resolved and has_valid_title:
            logger.info(f"Produto {product_id} já resolvido com sucesso antes. Pulando.")
            return {"status": "skipped", "reason": "already_resolved"}
    else:
        logger.info(f"Forçando re-resolução para produto {product_id}.")
    
    # 1. Obter normalizer e identity
    normalizer = get_normalizer()
    resolver = get_identity_resolver()
    fetch_service = get_product_fetch_service()
    
    # 2. Buscar dados reais (Cascading Resolver)
    gtin = product_data.get("gtin")
    sources = []
    enriched_data: Dict[str, Any] = {}
    
    if gtin:
        logger.info(f"Buscando dados reais via cascading resolver para GTIN {gtin}...")
        import asyncio
        lookup_result = asyncio.run(fetch_service.lookup_by_gtin(gtin))
        
        # Copiar dados do lookup para enriched_data (seja found ou fallback)
        if hasattr(lookup_result, "data") and lookup_result.data:
            for k, v in lookup_result.data.items():
                if v and v not in (None, "", [], {}):
                    enriched_data[k] = v
        
        if lookup_result.found:
            sources.append({"source_type": lookup_result.source})
            logger.info(f"GTIN {gtin} encontrado via {lookup_result.source} (confidence: {lookup_result.confidence})")
        else:
            # Não encontrou nas bases primárias, tentar pesquisa na internet
            logger.info(f"GTIN {gtin} não encontrado nas bases primárias. Tentando pesquisa na internet...")
            enrich_service = get_enrichment_service()
            try:
                internet_res = asyncio.run(enrich_service.search_product_on_internet(gtin))
            except Exception as e:
                logger.error(f"Erro na pesquisa na internet para {gtin}: {e}")
                internet_res = None
            
            if internet_res:
                logger.info(f"GTIN {gtin} resolvido via pesquisa na internet.")
                sources.append({"source_type": "internet_search"})
                # Sobrescrever dados do fallback com dados da internet
                for k, v in internet_res.items():
                    if v and k in ["title", "brand", "description", "category"]:
                        enriched_data[k] = v
            else:
                sources.append({"source_type": lookup_result.source})
                logger.info(f"GTIN {gtin} não encontrado em nenhuma fonte. Usando dados de fallback.")
        
        # Aplicar dados enriquecidos ao product_data
        for k, v in enriched_data.items():
            if _should_replace_field(k, product_data.get(k), v):
                product_data[k] = v
    else:
        sources.append({"source_type": "manual"})
    
    # 3. Normalizar
    normalized = normalizer.normalize_product(product_data)
    
    # 4. Calcular confidence
    ident = resolver.resolve_confidence(normalized, sources=sources)
    status = ident["status"]
    
    # 5. Salvar volta no supabase
    update_data: Dict[str, Any] = {
        "status": status,
        "confidence": ident["confidence"],
    }
    
    # Salvar os campos que foram enriquecidos pelo fetch service
    for field in ["title", "brand", "category", "description", "images", "attributes"]:
        value = normalized.get(field)
        if value and value not in (None, "", [], {}):
            update_data[field] = value
            
    logger.info(f"💾 Atualizando Supabase para {product_id}: status={status}, confidence={ident['confidence']}, campos={list(update_data.keys())}")
    res_update = supabase.table("products").update(update_data).eq("id", product_id).execute()
    
    if res_update.data:
        logger.info(f"✅ Supabase atualizado com sucesso para {product_id}.")
    else:
        logger.error(f"❌ Falha ao atualizar Supabase para {product_id}. Resposta: {res_update}")
    
    # 6. Enfileirar próxima etapa se ok
    if resolver.should_proceed_to_listing(ident):
        from rq import Queue
        from redis import Redis
        from packages.shared.config import get_settings
        q = Queue(connection=Redis.from_url(get_settings().redis_url))
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
