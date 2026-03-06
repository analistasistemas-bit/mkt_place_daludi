"""
Listing Builder — Montagem determinística de ListingDraft.
Combina: produto normalizado + template renderizado + pricing + compliance.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.listing_builder")


class ListingBuilder:
    """
    Monta ListingDraft determinístico combinando:
    1. Produto normalizado (normalizer)
    2. Copy renderizada (template_renderer)
    3. Preço calculado (pricing)
    4. Compliance verificado (compliance_rules)
    
    REGRA: este builder é 100% determinístico, zero IA.
    O LLM só é chamado DEPOIS, se compliance marcar spans.
    """

    def build(
        self,
        product: Dict[str, Any],
        rendered_copy: Dict[str, str],
        pricing_result: Optional[Dict[str, Any]] = None,
        compliance_result: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Monta ListingDraft com todos os dados combinados.
        
        Retorna dict pronto para INSERT na tabela listings.
        """
        product_id = product.get("id", str(uuid.uuid4()))
        idempotency_key = self._generate_idempotency_key(product, rendered_copy)

        # Determinar status baseado em compliance
        compliance_passed = True
        compliance_status = "passed"
        compliance_issues: List[Dict[str, Any]] = []

        if compliance_result:
            compliance_passed = compliance_result.get("passed", True)
            compliance_status = compliance_result.get("status", "passed")
            spans = compliance_result.get("spans", [])
            compliance_issues = [
                {
                    "text": getattr(s, "text", s.get("text", "")),
                    "reason": getattr(s, "reason", s.get("reason", "")),
                    "category": getattr(s, "category", s.get("category", "")),
                    "severity": getattr(s, "severity", s.get("severity", "")),
                }
                for s in spans
            ]

        # Determinar status do listing
        if compliance_passed:
            listing_status = "ready"
        else:
            high_severity = any(
                i.get("severity") == "high" for i in compliance_issues
            )
            listing_status = "pending_review" if high_severity else "draft"

        # Preço
        price = None
        currency = "BRL"
        if pricing_result:
            price = pricing_result.get("suggested_price")
            currency = pricing_result.get("currency", "BRL")

        # Montar listing
        listing = {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id or product.get("tenant_id", ""),
            "product_id": str(product_id),
            "idempotency_key": idempotency_key,
            "title": rendered_copy.get("title", ""),
            "description": rendered_copy.get("description", ""),
            "price": price,
            "currency": currency,
            "category_id": product.get("ml_category_id"),
            "status": listing_status,
            "compliance_status": compliance_status,
            "compliance_issues": compliance_issues,
            "version": 1,
            "attributes": self._build_listing_attributes(product),
            "images": product.get("images", []),
            "metadata": {
                "template_used": rendered_copy.get("template_used"),
                "template_version": rendered_copy.get("template_version"),
                "pricing_strategy": pricing_result.get("strategy") if pricing_result else None,
                "confidence": product.get("confidence"),
                "source_gtin": product.get("gtin"),
            },
        }

        logger.info(
            f"ListingDraft montado: status={listing_status}, compliance={compliance_status}",
            extra={"extra_data": {
                "product_id": str(product_id),
                "gtin": product.get("gtin"),
                "listing_status": listing_status,
                "compliance_issues": len(compliance_issues),
                "tenant_id": tenant_id,
            }},
        )

        return listing

    def _generate_idempotency_key(
        self, product: Dict[str, Any], rendered_copy: Dict[str, str]
    ) -> str:
        """Gera idempotency key baseada no conteúdo (evita duplicatas)."""
        content = (
            f"{product.get('gtin', '')}:"
            f"{product.get('tenant_id', '')}:"
            f"{rendered_copy.get('title', '')}:"
            f"{rendered_copy.get('template_version', '')}"
        )
        return f"listing-{hashlib.md5(content.encode()).hexdigest()[:12]}"

    def _build_listing_attributes(self, product: Dict[str, Any]) -> Dict[str, Any]:
        """Monta atributos do listing a partir do produto."""
        attrs = product.get("attributes", {})
        listing_attrs: Dict[str, Any] = {}

        # Mapear atributos comuns para formato ML
        attr_map = {
            "brand": "BRAND",
            "model": "MODEL",
            "color": "COLOR",
            "size": "SIZE",
            "weight": "WEIGHT",
            "material": "MATERIAL",
            "condition": "ITEM_CONDITION",
        }

        for product_key, ml_key in attr_map.items():
            value = attrs.get(product_key) or product.get(product_key)
            if value:
                listing_attrs[ml_key] = value

        return listing_attrs


# Singleton
_listing_builder: Optional[ListingBuilder] = None


def get_listing_builder() -> ListingBuilder:
    """Factory singleton."""
    global _listing_builder
    if _listing_builder is None:
        _listing_builder = ListingBuilder()
    return _listing_builder
