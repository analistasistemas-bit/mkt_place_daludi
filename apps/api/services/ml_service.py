"""
Mercado Livre Service — Integração com API do Mercado Livre.
Stub funcional: retorna dados simulados com a interface pronta.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.ml")


@dataclass
class MLListingResult:
    """Resultado de busca de anúncio similar no ML."""
    ml_item_id: str
    title: str
    price: float
    currency: str
    seller_id: str
    condition: str
    category_id: str
    permalink: str
    thumbnail: str
    sold_quantity: int
    available_quantity: int


@dataclass
class MLPublishResult:
    """Resultado de publicação de anúncio no ML."""
    success: bool
    ml_item_id: Optional[str] = None
    permalink: Optional[str] = None
    error: Optional[str] = None


class MLService:
    """
    Serviço de integração com o Mercado Livre.
    
    Stub funcional com interface pronta para integração real via API ML.
    Em produção: usar ML_CLIENT_ID/SECRET para OAuth2 e acessar endpoints reais.
    """

    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        self._client_id = client_id
        self._client_secret = client_secret
        self._access_token: Optional[str] = None

    async def search_similar_listings(
        self,
        query: str,
        category_id: Optional[str] = None,
        limit: int = 10,
    ) -> List[MLListingResult]:
        """
        Busca anúncios similares no Mercado Livre.
        
        STUB: Retorna resultados simulados.
        PRODUÇÃO: GET /sites/MLB/search?q={query}&category={category_id}
        """
        logger.info(
            "ML busca similar (stub)",
            extra={"extra_data": {"query": query, "category": category_id}},
        )

        # Stub: gerar 3 resultados simulados
        results = []
        for i in range(min(limit, 3)):
            results.append(MLListingResult(
                ml_item_id=f"MLB{uuid.uuid4().hex[:8].upper()}",
                title=f"{query} - Variação {i + 1}",
                price=99.90 + (i * 50),
                currency="BRL",
                seller_id=f"SELLER{i}",
                condition="new",
                category_id=category_id or "MLB1000",
                permalink=f"https://www.mercadolivre.com.br/stub-{i}",
                thumbnail=f"https://http2.mlstatic.com/stub-{i}.jpg",
                sold_quantity=(i + 1) * 10,
                available_quantity=100 - (i * 20),
            ))

        return results

    async def publish_listing(
        self,
        tenant_id: str,
        listing_data: Dict[str, Any],
        access_token: Optional[str] = None,
    ) -> MLPublishResult:
        """
        Publica anúncio no Mercado Livre.
        
        STUB: Retorna sucesso simulado.
        PRODUÇÃO: POST /items com OAuth2.
        """
        logger.info(
            "ML publicação (stub)",
            extra={"extra_data": {
                "tenant_id": tenant_id,
                "title": listing_data.get("title", ""),
            }},
        )

        # Stub: simular publicação
        fake_id = f"MLB{uuid.uuid4().hex[:10].upper()}"
        return MLPublishResult(
            success=True,
            ml_item_id=fake_id,
            permalink=f"https://www.mercadolivre.com.br/{fake_id}",
        )

    async def update_price(
        self,
        ml_item_id: str,
        new_price: float,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Atualiza preço de anúncio existente.
        
        STUB: Retorna sucesso.
        PRODUÇÃO: PUT /items/{id} com {price: new_price}
        """
        logger.info(
            "ML update preço (stub)",
            extra={"extra_data": {"ml_item_id": ml_item_id, "new_price": new_price}},
        )
        return {"success": True, "ml_item_id": ml_item_id, "new_price": new_price}

    async def update_stock(
        self,
        ml_item_id: str,
        available_quantity: int,
        access_token: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Atualiza estoque de anúncio existente.
        
        STUB: Retorna sucesso.
        PRODUÇÃO: PUT /items/{id} com {available_quantity}
        """
        logger.info(
            "ML update estoque (stub)",
            extra={"extra_data": {"ml_item_id": ml_item_id, "quantity": available_quantity}},
        )
        return {"success": True, "ml_item_id": ml_item_id, "available_quantity": available_quantity}

    async def get_categories(
        self, site_id: str = "MLB"
    ) -> List[Dict[str, Any]]:
        """
        Lista categorias do Mercado Livre.
        
        STUB: Retorna categorias básicas.
        PRODUÇÃO: GET /sites/{site_id}/categories
        """
        return [
            {"id": "MLB1051", "name": "Celulares e Telefones"},
            {"id": "MLB1648", "name": "Computadores"},
            {"id": "MLB1574", "name": "Casa, Móveis e Decoração"},
            {"id": "MLB1246", "name": "Beleza e Cuidado Pessoal"},
            {"id": "MLB1000", "name": "Eletrônicos, Áudio e Vídeo"},
        ]


# Singleton
_ml_service: Optional[MLService] = None


def get_ml_service() -> MLService:
    """Factory singleton para MLService."""
    global _ml_service
    if _ml_service is None:
        _ml_service = MLService()
    return _ml_service
