"""
Pipeline Orchestrator — Executa o fluxo completo de geração de listing.
Ordem obrigatória: rules → templates → cache → vector reuse → AI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from apps.api.services.compliance_rules import ComplianceRules, get_compliance_rules
from apps.api.services.gs1_service import GS1Service, get_gs1_service
from apps.api.services.identity_resolver import IdentityResolver, get_identity_resolver
from apps.api.services.listing_builder import ListingBuilder, get_listing_builder
from apps.api.services.llm_service import LLMService, get_llm_service
from apps.api.services.ml_service import MLService, get_ml_service
from apps.api.services.normalizer import Normalizer, get_normalizer
from apps.api.services.pricing import PricingService, get_pricing_service
from apps.api.services.template_renderer import TemplateRenderer, get_template_renderer
from apps.api.services.vector_service import VectorService, get_vector_service
from packages.shared.logging import get_logger

logger = get_logger("service.pipeline")


@dataclass
class PipelineResult:
    """Resultado completo de execução do pipeline."""
    success: bool
    listing: Optional[Dict[str, Any]] = None
    stage: str = ""  # Estágio onde parou
    error: Optional[str] = None
    stages_completed: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class Pipeline:
    """
    Orquestrador do pipeline de geração de listings.
    
    Ordem OBRIGATÓRIA (CLAUDE.md):
    1. RULES: normalizar + resolver identidade + compliance
    2. TEMPLATES: renderizar copy via template da categoria
    3. CACHE: verificar se listing já existe (idempotência)
    4. VECTOR REUSE: buscar copies similares aprovadas (pgvector)
    5. AI: somente se necessário (compliance spans ou polimento)
    
    IA é ÚLTIMO RECURSO. Se os passos 1-4 resolvem → zero LLM.
    """

    def __init__(
        self,
        normalizer: Optional[Normalizer] = None,
        identity_resolver: Optional[IdentityResolver] = None,
        gs1_service: Optional[GS1Service] = None,
        ml_service: Optional[MLService] = None,
        pricing_service: Optional[PricingService] = None,
        template_renderer: Optional[TemplateRenderer] = None,
        compliance_rules: Optional[ComplianceRules] = None,
        listing_builder: Optional[ListingBuilder] = None,
        llm_service: Optional[LLMService] = None,
        vector_service: Optional[VectorService] = None,
    ):
        self.normalizer = normalizer or get_normalizer()
        self.identity_resolver = identity_resolver or get_identity_resolver()
        self.gs1_service = gs1_service or get_gs1_service()
        self.ml_service = ml_service or get_ml_service()
        self.pricing_service = pricing_service or get_pricing_service()
        self.template_renderer = template_renderer or get_template_renderer()
        self.compliance_rules = compliance_rules or get_compliance_rules()
        self.listing_builder = listing_builder or get_listing_builder()
        self.llm_service = llm_service or get_llm_service()
        self.vector_service = vector_service or get_vector_service()

    async def execute(
        self,
        product_data: Dict[str, Any],
        tenant_id: str,
        sources: Optional[List[Dict[str, Any]]] = None,
        tenant_settings: Optional[Dict[str, Any]] = None,
    ) -> PipelineResult:
        """
        Executa pipeline completo para um produto.
        
        Fluxo: rules → templates → cache → vector → AI
        """
        stages_completed: List[str] = []

        try:
            # ══════════════════════════════════════════════════
            # ETAPA 1: RULES — Normalização + Identidade + Compliance
            # ══════════════════════════════════════════════════

            logger.info(
                "Pipeline: ETAPA 1 — RULES",
                extra={"extra_data": {
                    "gtin": product_data.get("gtin"),
                    "tenant_id": tenant_id,
                }},
            )

            # 1a. Normalizar atributos do produto
            normalized = self.normalizer.normalize_product(product_data)
            stages_completed.append("normalize")

            # 1b. Resolver identidade → score de confiança
            identity_result = self.identity_resolver.resolve_confidence(
                normalized, sources=sources or []
            )
            normalized["confidence"] = identity_result["confidence"]
            normalized["identity_status"] = identity_result["status"]
            stages_completed.append("identity_resolve")

            # Verificar se pode prosseguir
            if not self.identity_resolver.should_proceed_to_listing(identity_result):
                return PipelineResult(
                    success=False,
                    stage="identity_resolve",
                    error=f"Produto bloqueado: score {identity_result['confidence']}. "
                          f"Sugestões: {identity_result['suggestions']}",
                    stages_completed=stages_completed,
                    metadata={"identity": identity_result},
                )

            # ══════════════════════════════════════════════════
            # ETAPA 2: TEMPLATES — Renderizar copy
            # ══════════════════════════════════════════════════

            logger.info("Pipeline: ETAPA 2 — TEMPLATES")

            rendered_copy = await self.template_renderer.render(
                normalized,
                category=normalized.get("category"),
                tenant_id=tenant_id,
            )
            stages_completed.append("template_render")

            # ══════════════════════════════════════════════════
            # ETAPA 3: CACHE — Verificar se já existe
            # ══════════════════════════════════════════════════

            logger.info("Pipeline: ETAPA 3 — CACHE")

            # Calcular pricing
            competitors_data = await self.ml_service.search_similar_listings(
                query=normalized.get("title", ""),
                category_id=normalized.get("ml_category_id"),
                limit=5,
            )
            competitor_prices = [
                {"price": c.price, "seller": c.seller_id}
                for c in competitors_data
            ]

            pricing_result = self.pricing_service.calculate_price(
                normalized, competitors=competitor_prices, tenant_settings=tenant_settings
            )
            stages_completed.append("pricing")

            # ══════════════════════════════════════════════════
            # ETAPA 4: VECTOR REUSE — Buscar copies aprovadas
            # ══════════════════════════════════════════════════

            logger.info("Pipeline: ETAPA 4 — VECTOR REUSE")

            similar_copies = await self.vector_service.find_similar_copies(
                text=rendered_copy.get("description", ""),
                category=normalized.get("category"),
                tenant_id=tenant_id,
            )

            # Se encontrou copy similar aprovada → reutilizar (zero LLM)
            if similar_copies and similar_copies[0].similarity >= 0.85:
                best_copy = similar_copies[0]
                rendered_copy["description"] = best_copy.content
                rendered_copy["_vector_reused"] = True
                rendered_copy["_reused_copy_id"] = best_copy.id
                rendered_copy["_similarity"] = best_copy.similarity
                logger.info(
                    f"Vector reuse: copy reutilizada (sim={best_copy.similarity:.2f})",
                    extra={"extra_data": {"copy_id": best_copy.id}},
                )
            stages_completed.append("vector_reuse")

            # ══════════════════════════════════════════════════
            # COMPLIANCE CHECK (antes de decidir se precisa AI)
            # ══════════════════════════════════════════════════

            compliance_result = self.compliance_rules.check(
                title=rendered_copy.get("title", ""),
                description=rendered_copy.get("description", ""),
                category=normalized.get("category"),
            )
            stages_completed.append("compliance_check")

            # ══════════════════════════════════════════════════
            # ETAPA 5: AI — Somente se necessário
            # ══════════════════════════════════════════════════

            llm_used = False

            if not compliance_result.passed and compliance_result.spans:
                logger.info(
                    f"Pipeline: ETAPA 5 — AI (compliance rewrite: {len(compliance_result.spans)} spans)"
                )

                # Reescrever spans de compliance via LLM
                spans_data = [
                    {
                        "text": s.text,
                        "reason": s.reason,
                        "start_pos": s.start_pos,
                        "end_pos": s.end_pos,
                    }
                    for s in compliance_result.spans
                ]

                rewrite_results = await self.llm_service.rewrite_compliance_spans(spans_data)

                # Aplicar reescritas na description
                description = rendered_copy.get("description", "")
                for rewrite in reversed(rewrite_results):
                    description = description.replace(
                        rewrite.original, rewrite.rewritten
                    )
                rendered_copy["description"] = description
                llm_used = True

                # Re-check compliance após rewrite
                compliance_result = self.compliance_rules.check(
                    title=rendered_copy.get("title", ""),
                    description=rendered_copy["description"],
                    category=normalized.get("category"),
                )
                compliance_result.status = "rewritten"
                stages_completed.append("ai_compliance_rewrite")

            # Comprimir título se necessário
            title = rendered_copy.get("title", "")
            if len(title) > 60:
                compressed = await self.llm_service.compress_title(title)
                rendered_copy["title"] = compressed
                llm_used = True
                stages_completed.append("ai_compress_title")

            if not llm_used:
                logger.info("Pipeline: ETAPA 5 — AI SKIPPED (não necessário)")
                stages_completed.append("ai_skipped")

            # ══════════════════════════════════════════════════
            # MONTAR LISTING DRAFT
            # ══════════════════════════════════════════════════

            # Converter dataclass para dict para pricing
            pricing_dict = {
                "suggested_price": pricing_result.suggested_price,
                "min_price": pricing_result.min_price,
                "max_price": pricing_result.max_price,
                "strategy": pricing_result.strategy,
                "currency": pricing_result.currency,
            }

            listing = self.listing_builder.build(
                product=normalized,
                rendered_copy=rendered_copy,
                pricing_result=pricing_dict,
                compliance_result={
                    "passed": compliance_result.passed,
                    "status": compliance_result.status,
                    "spans": compliance_result.spans,
                },
                tenant_id=tenant_id,
            )
            stages_completed.append("listing_build")

            logger.info(
                f"Pipeline concluído com sucesso — LLM {'usado' if llm_used else 'NÃO usado'}",
                extra={"extra_data": {
                    "gtin": product_data.get("gtin"),
                    "listing_status": listing.get("status"),
                    "llm_used": llm_used,
                    "stages": stages_completed,
                }},
            )

            return PipelineResult(
                success=True,
                listing=listing,
                stage="complete",
                stages_completed=stages_completed,
                metadata={
                    "identity": identity_result,
                    "pricing": pricing_dict,
                    "compliance_passed": compliance_result.passed,
                    "llm_used": llm_used,
                    "vector_reused": rendered_copy.get("_vector_reused", False),
                },
            )

        except Exception as e:
            logger.error(
                f"Pipeline falhou na etapa '{stages_completed[-1] if stages_completed else 'init'}'",
                extra={"extra_data": {
                    "error": str(e),
                    "stages_completed": stages_completed,
                    "gtin": product_data.get("gtin"),
                }},
            )
            return PipelineResult(
                success=False,
                stage=stages_completed[-1] if stages_completed else "init",
                error=str(e),
                stages_completed=stages_completed,
            )


# Singleton
_pipeline: Optional[Pipeline] = None


def get_pipeline() -> Pipeline:
    """Factory singleton."""
    global _pipeline
    if _pipeline is None:
        _pipeline = Pipeline()
    return _pipeline
