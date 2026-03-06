"""
Identity Resolver — Score de confiança do produto resolvido.
Calcula confiança baseada em completude de campos, qualidade de fontes, e evidências.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.identity_resolver")


# Pesos de confiança por campo
FIELD_WEIGHTS = {
    "title": 0.20,
    "brand": 0.15,
    "category": 0.10,
    "description": 0.10,
    "images": 0.15,        # pelo menos 1 imagem
    "attributes": 0.10,    # atributos preenchidos
    "gtin_valid": 0.10,    # GTIN válido com dígito verificador
    "sources": 0.10,       # múltiplas fontes = mais confiável
}

# Peso por tipo de fonte
SOURCE_WEIGHTS = {
    "gs1": 1.0,         # Fonte oficial, máxima confiança
    "cnp": 0.9,         # Cadastro nacional
    "verified": 0.85,   # Verificação manual
    "openfoodfacts": 0.7,# DB aberto
    "mercadolivre": 0.6, # Scraping ML
    "google": 0.5,       # Google enrichment
    "manual": 0.4,       # Entrada manual
    "stub": 0.3,         # Dados stub
    "fallback": 0.2,     # Fallback local
}

# Threshold de status
CONFIDENCE_THRESHOLDS = {
    "resolved": 0.7,      # >= 0.7: resolvido
    "needs_review": 0.1,  # >= 0.1: precisa revisão
    # < 0.1: bloqueado
}


class IdentityResolver:
    """
    Calcula score de confiança de um produto resolvido.
    
    Score [0.0 - 1.0] baseado em:
    1. Completude de campos (title, brand, images, etc.)
    2. Qualidade das fontes (GS1 > CNP > ML > manual)
    3. Quantidade de evidências cruzadas
    4. Consistência entre fontes
    """

    def resolve_confidence(
        self,
        product: Dict[str, Any],
        sources: Optional[List[Dict[str, Any]]] = None,
        evidence: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Calcula score de confiança e determina status do produto.
        
        Retorna:
            {
                "confidence": 0.75,
                "status": "resolved",
                "breakdown": { campo: score },
                "suggestions": ["Adicionar imagens para aumentar score"]
            }
        """
        sources = sources or []
        evidence = evidence or []

        breakdown: Dict[str, float] = {}
        suggestions: List[str] = []

        # 1. Completude de campos
        breakdown["title"] = FIELD_WEIGHTS["title"] if product.get("title") else 0.0
        if not product.get("title"):
            suggestions.append("Adicionar título do produto")

        breakdown["brand"] = FIELD_WEIGHTS["brand"] if product.get("brand") else 0.0
        if not product.get("brand"):
            suggestions.append("Adicionar marca do produto")

        breakdown["category"] = FIELD_WEIGHTS["category"] if product.get("category") else 0.0
        if not product.get("category"):
            suggestions.append("Definir categoria do produto")

        breakdown["description"] = FIELD_WEIGHTS["description"] if product.get("description") else 0.0
        if not product.get("description"):
            suggestions.append("Adicionar descrição")

        # Imagens: pontuação parcial
        images = product.get("images", [])
        if len(images) >= 3:
            breakdown["images"] = FIELD_WEIGHTS["images"]
        elif len(images) >= 1:
            breakdown["images"] = FIELD_WEIGHTS["images"] * 0.6
            suggestions.append(f"Adicionar mais imagens ({len(images)}/3 mínimo)")
        else:
            breakdown["images"] = 0.0
            suggestions.append("Adicionar pelo menos 1 imagem do produto")

        # Atributos
        attrs = product.get("attributes", {})
        if len(attrs) >= 3:
            breakdown["attributes"] = FIELD_WEIGHTS["attributes"]
        elif len(attrs) >= 1:
            breakdown["attributes"] = FIELD_WEIGHTS["attributes"] * 0.5
            suggestions.append("Adicionar mais atributos técnicos")
        else:
            breakdown["attributes"] = 0.0
            suggestions.append("Adicionar atributos do produto")

        # GTIN válido
        gtin = product.get("gtin", "")
        breakdown["gtin_valid"] = FIELD_WEIGHTS["gtin_valid"] if len(gtin) in (8, 12, 13, 14) else 0.0

        # 2. Qualidade de fontes
        if sources:
            best_source_weight = max(
                SOURCE_WEIGHTS.get(s.get("source_type", "manual"), 0.3)
                for s in sources
            )
            # Bonus para múltiplas fontes
            multi_source_bonus = min(len(sources) * 0.1, 0.3)
            breakdown["sources"] = FIELD_WEIGHTS["sources"] * (best_source_weight + multi_source_bonus)
        else:
            breakdown["sources"] = 0.0
            suggestions.append("Validar com fontes adicionais (GS1, CNP)")

        # 3. Calcular score total
        total_confidence = min(sum(breakdown.values()), 1.0)

        # 4. Determinar status
        if total_confidence >= CONFIDENCE_THRESHOLDS["resolved"]:
            status = "resolved"
        elif total_confidence >= CONFIDENCE_THRESHOLDS["needs_review"]:
            status = "needs_review"
        else:
            status = "blocked"

        result = {
            "confidence": round(total_confidence, 3),
            "status": status,
            "breakdown": {k: round(v, 3) for k, v in breakdown.items()},
            "suggestions": suggestions,
            "sources_count": len(sources),
            "evidence_count": len(evidence),
        }

        logger.info(
            f"Identity resolved: {status} ({total_confidence:.2f})",
            extra={"extra_data": {
                "gtin": product.get("gtin"),
                "confidence": total_confidence,
                "status": status,
            }},
        )

        return result

    def should_proceed_to_listing(self, confidence_result: Dict[str, Any]) -> bool:
        """Verifica se o produto pode avançar para geração de listing."""
        return confidence_result.get("status") in ("resolved", "needs_review")


# Singleton
_identity_resolver: Optional[IdentityResolver] = None


def get_identity_resolver() -> IdentityResolver:
    """Factory singleton."""
    global _identity_resolver
    if _identity_resolver is None:
        _identity_resolver = IdentityResolver()
    return _identity_resolver
