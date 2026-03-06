"""
GS1 Service — Consulta de GTINs via GS1/CNP.
Stub funcional: retorna dados simulados com a interface pronta para integração real.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.gs1")


@dataclass
class GTINLookupResult:
    """Resultado de consulta GS1."""
    gtin: str
    found: bool
    source: str  # "gs1" | "cnp" | "stub"
    confidence: float  # 0.0 - 1.0
    data: Dict[str, Any]


class GS1Service:
    """
    Serviço de consulta GS1/CNP para resolução de GTIN.
    
    Stub funcional: retorna dados simulados baseados no padrão do GTIN.
    Em produção, integrar com API GS1 Brasil e Cadastro Nacional de Produtos.
    """

    # Prefixos GS1 por país (789 = Brasil)
    BRAZIL_PREFIXES = ("789", "790")

    def __init__(self):
        self._cache: Dict[str, GTINLookupResult] = {}

    def validate_gtin(self, gtin: str) -> bool:
        """Valida formato e dígito verificador do GTIN."""
        cleaned = re.sub(r"[^0-9]", "", gtin)
        if len(cleaned) not in (8, 12, 13, 14):
            return False
        return self._check_digit(cleaned)

    def _check_digit(self, gtin: str) -> bool:
        """Verifica dígito de controle GTIN (módulo 10)."""
        digits = [int(d) for d in gtin]
        check = digits[-1]
        total = 0
        for i, d in enumerate(digits[:-1]):
            weight = 3 if (len(digits) - 1 - i) % 2 == 0 else 1
            total += d * weight
        expected = (10 - (total % 10)) % 10
        return check == expected

    def is_brazilian(self, gtin: str) -> bool:
        """Verifica se o GTIN é de produto brasileiro."""
        cleaned = re.sub(r"[^0-9]", "", gtin)
        if len(cleaned) == 13:
            return cleaned[:3] in self.BRAZIL_PREFIXES
        return False

    async def lookup_by_gtin(
        self, gtin: str, tenant_id: Optional[str] = None
    ) -> GTINLookupResult:
        """
        Consulta dados do produto pelo GTIN.
        
        STUB: Retorna dados simulados baseados no padrão do GTIN.
        PRODUÇÃO: Consultar API GS1 Brasil → CNP → fallback.
        """
        cleaned = re.sub(r"[^0-9]", "", gtin)

        # Cache em memória
        if cleaned in self._cache:
            logger.info("GS1 cache hit", extra={"extra_data": {"gtin": cleaned}})
            return self._cache[cleaned]

        if not self.validate_gtin(cleaned):
            return GTINLookupResult(
                gtin=cleaned,
                found=False,
                source="validation",
                confidence=0.0,
                data={"error": "GTIN inválido"},
            )

        # STUB: gerar dados simulados
        result = self._generate_stub_data(cleaned)

        logger.info(
            "GS1 lookup realizado (stub)",
            extra={"extra_data": {
                "gtin": cleaned,
                "found": result.found,
                "source": result.source,
                "tenant_id": tenant_id,
            }},
        )

        self._cache[cleaned] = result
        return result

    async def validate_gtin_owner(
        self, gtin: str, company_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Valida se o GTIN pertence à empresa.
        
        STUB: Sempre retorna válido.
        PRODUÇÃO: Consultar GS1 para verificar propriedade.
        """
        return {
            "gtin": gtin,
            "valid": True,
            "owner": company_id or "stub_company",
            "source": "stub",
        }

    def _generate_stub_data(self, gtin: str) -> GTINLookupResult:
        """Gera dados stub baseados no prefixo do GTIN."""
        is_br = self.is_brazilian(gtin)

        # Categorias simuladas baseadas no 4º dígito
        category_map = {
            "0": "eletronicos",
            "1": "eletronicos",
            "2": "alimentos",
            "3": "beleza",
            "4": "casa",
            "5": "vestuario",
            "6": "eletronicos",
            "7": "casa",
            "8": "beleza",
            "9": "eletronicos",
        }

        fourth_digit = gtin[3] if len(gtin) > 3 else "0"
        category = category_map.get(fourth_digit, "geral")

        return GTINLookupResult(
            gtin=gtin,
            found=True,
            source="stub",
            confidence=0.7,
            data={
                "gtin": gtin,
                "title": f"Produto {gtin[-4:]}",
                "brand": "Marca Teste" if is_br else "Test Brand",
                "category": category,
                "description": f"Produto com GTIN {gtin}",
                "country": "BR" if is_br else "XX",
                "attributes": {
                    "weight": "500g",
                    "dimensions": "20x15x10cm",
                },
                "images": [],
            },
        )


# Singleton
_gs1_service: Optional[GS1Service] = None


def get_gs1_service() -> GS1Service:
    """Factory singleton para GS1Service."""
    global _gs1_service
    if _gs1_service is None:
        _gs1_service = GS1Service()
    return _gs1_service
