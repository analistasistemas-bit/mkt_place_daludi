"""
Product Fetch Service — Consulta de GTINs em cascata (OpenFoodFacts -> Mercado Livre Search -> Fallback).
Substitui o antigo gs1_service usando fontes reais gratuitas para resolver o produto.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
import httpx

from packages.shared.logging import get_logger

logger = get_logger("service.product_fetch")


@dataclass
class GTINLookupResult:
    """Resultado de consulta em cascata do produto por GTIN."""
    gtin: str
    found: bool
    source: str  # "openfoodfacts" | "mercadolivre" | "fallback"
    confidence: float  # 0.0 - 1.0
    data: Dict[str, Any]


class ProductFetchService:
    """
    Serviço de consulta de produto em cascata para resolução de GTIN.
    
    Ordem de fallback:
    1. OpenFoodFacts (Ótimo para alimentos) - 70% confidence
    2. Mercado Livre Search (Busca pública) - 50% confidence
    3. Fallback (Dados vazios para revisão) - 14% confidence
    """

    def __init__(self):
        self._cache: Dict[str, GTINLookupResult] = {}
        # Cliente HTTP reutilizável
        self._http_client = httpx.AsyncClient(timeout=10.0)

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
        weight = 3
        for d in reversed(digits[:-1]):
            total += d * weight
            weight = 1 if weight == 3 else 3
            
        expected = (10 - (total % 10)) % 10
        return check == expected

    async def lookup_by_gtin(
        self, gtin: str, tenant_id: Optional[str] = None
    ) -> GTINLookupResult:
        """
        Consulta dados do produto pelo GTIN em cascata.
        """
        cleaned = re.sub(r"[^0-9]", "", gtin)

        # Cache em memória
        if cleaned in self._cache:
            logger.info("Product fetch cache hit", extra={"extra_data": {"gtin": cleaned}})
            return self._cache[cleaned]

        if not self.validate_gtin(cleaned):
            return GTINLookupResult(
                gtin=cleaned,
                found=False,
                source="validation",
                confidence=0.0,
                data={"error": "GTIN inválido"},
            )

        # 1. Tentar OpenFoodFacts
        off_result = await self._fetch_openfoodfacts(cleaned)
        if off_result:
            self._cache[cleaned] = off_result
            return off_result

        # 2. Tentar Mercado Livre Search
        ml_result = await self._fetch_mercadolivre(cleaned)
        if ml_result:
            self._cache[cleaned] = ml_result
            return ml_result

        # 3. Fallback
        fallback_result = self._fetch_fallback(cleaned)
        self._cache[cleaned] = fallback_result
        return fallback_result

    async def _fetch_openfoodfacts(self, gtin: str) -> Optional[GTINLookupResult]:
        """Consulta API do OpenFoodFacts."""
        url = f"https://world.openfoodfacts.org/api/v2/product/{gtin}.json"
        try:
            response = await self._http_client.get(url)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == 1 and "product" in data:
                    product = data["product"]
                    
                    product_name = product.get("product_name") or product.get("product_name_pt") or ""
                    if not product_name:
                        return None
                    
                    brands = product.get("brands", "")
                    categories = product.get("categories", "")
                    ingredients = product.get("ingredients_text", "")
                    quantity = product.get("quantity", "")
                    image_url = product.get("image_url", "")
                    
                    description = ingredients
                    if quantity:
                        description = f"Quantidade: {quantity}\n\nIngredientes: {ingredients}"

                    return GTINLookupResult(
                        gtin=gtin,
                        found=True,
                        source="openfoodfacts",
                        confidence=0.70,
                        data={
                            "gtin": gtin,
                            "title": product_name,
                            "brand": brands,
                            "category": categories.split(",")[0] if categories else "",
                            "description": description.strip(),
                            "attributes": {
                                "quantity": quantity
                            },
                            "images": [image_url] if image_url else [],
                        }
                    )
        except Exception as e:
            logger.error(f"Erro ao consultar OpenFoodFacts para {gtin}: {e}")
        return None

    async def _fetch_mercadolivre(self, gtin: str) -> Optional[GTINLookupResult]:
        """Consulta busca pública do Mercado Livre."""
        url = f"https://api.mercadolibre.com/sites/MLB/search?q={gtin}"
        try:
            response = await self._http_client.get(url)
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if results:
                    best_match = results[0]  # Pega o primeiro e o mais relevante
                    
                    title = best_match.get("title", "")
                    category_id = best_match.get("category_id", "")
                    thumbnail = best_match.get("thumbnail", "").replace("-I.jpg", "-O.jpg") # Pega a versão em alta resolução
                    
                    # Extrair atributos, caso existam
                    attributes = best_match.get("attributes", [])
                    brand = ""
                    attrs_dict = {}
                    for attr in attributes:
                        if attr.get("id") == "BRAND":
                            brand = attr.get("value_name", "")
                        else:
                            attrs_dict[attr.get("name")] = attr.get("value_name")

                    return GTINLookupResult(
                        gtin=gtin,
                        found=True,
                        source="mercadolivre",
                        confidence=0.50,
                        data={
                            "gtin": gtin,
                            "title": title,
                            "brand": brand,
                            "category": category_id,
                            "description": f"Encontrado via ML Search. GTIN: {gtin}",
                            "attributes": attrs_dict,
                            "images": [thumbnail] if thumbnail else [],
                        }
                    )
        except Exception as e:
            logger.error(f"Erro ao consultar Mercado Livre para {gtin}: {e}")
        return None

    def _fetch_fallback(self, gtin: str) -> GTINLookupResult:
        """Retorna estrutura de fallback vazio quando nada for encontrado."""
        return GTINLookupResult(
            gtin=gtin,
            found=False,
            source="fallback",
            confidence=0.14,
            data={
                "gtin": gtin,
                "title": "Produto Sem Título Gerado",
                "brand": "",
                "category": "",
                "description": "",
                "attributes": {},
                "images": [],
            }
        )

    async def close(self):
        """Fecha o cliente HTTP associado."""
        await self._http_client.aclose()


# Singleton
_product_fetch_service: Optional[ProductFetchService] = None

def get_product_fetch_service() -> ProductFetchService:
    """Factory singleton para ProductFetchService."""
    global _product_fetch_service
    if _product_fetch_service is None:
        _product_fetch_service = ProductFetchService()
    return _product_fetch_service
