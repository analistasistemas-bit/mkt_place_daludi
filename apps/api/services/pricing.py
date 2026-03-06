"""
Pricing Service — Cálculo de preço baseado em concorrência.
Lógica 100% determinística. IA NUNCA decide preço.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.pricing")


@dataclass
class PricingResult:
    """Resultado do cálculo de preço."""
    suggested_price: float
    min_price: float
    max_price: float
    strategy: str  # "competitive" | "cost_plus" | "market_average"
    competitors_count: int
    margin_percent: float
    currency: str
    breakdown: Dict[str, Any]


class PricingService:
    """
    Cálculo de preço determinístico baseado em concorrência.
    
    REGRA ABSOLUTA (CLAUDE.md): IA NUNCA decide preço.
    
    Estratégias:
    1. Competitivo: preço do concorrente médio - margem de vantagem
    2. Custo + Margem: custo do produto + margem configurável
    3. Média de mercado: média dos concorrentes
    
    Fallback: custo + margem padrão (30%)
    """

    DEFAULT_MARGIN = 0.30          # 30%
    MIN_MARGIN = 0.10              # 10% mínimo
    COMPETITIVE_DISCOUNT = 0.05   # 5% abaixo da média

    def calculate_price(
        self,
        product: Dict[str, Any],
        competitors: Optional[List[Dict[str, Any]]] = None,
        tenant_settings: Optional[Dict[str, Any]] = None,
    ) -> PricingResult:
        """
        Calcula preço sugerido para o produto.
        
        Prioridade:
        1. Se há concorrentes → preço competitivo
        2. Se há custo → custo + margem
        3. Fallback → bloqueado (preço manual requerido)
        """
        settings = tenant_settings or {}
        margin = settings.get("default_margin", self.DEFAULT_MARGIN)
        min_margin = settings.get("min_margin", self.MIN_MARGIN)
        currency = settings.get("currency", "BRL")

        cost = product.get("cost")
        competitors = competitors or []
        valid_competitors = [c for c in competitors if c.get("price", 0) > 0]

        # Estratégia 1: Competitivo (se há concorrentes)
        if valid_competitors:
            return self._competitive_pricing(
                cost, valid_competitors, margin, min_margin, currency
            )

        # Estratégia 2: Custo + Margem
        if cost and cost > 0:
            return self._cost_plus_pricing(cost, margin, currency)

        # Fallback: sem dados suficientes
        logger.warning(
            "Sem dados para precificação",
            extra={"extra_data": {"gtin": product.get("gtin")}},
        )
        return PricingResult(
            suggested_price=0.0,
            min_price=0.0,
            max_price=0.0,
            strategy="manual_required",
            competitors_count=0,
            margin_percent=0.0,
            currency=currency,
            breakdown={"reason": "Sem custo nem concorrentes. Preço manual necessário."},
        )

    def _competitive_pricing(
        self,
        cost: Optional[float],
        competitors: List[Dict[str, Any]],
        margin: float,
        min_margin: float,
        currency: str,
    ) -> PricingResult:
        """Calcula preço competitivo baseado nos concorrentes."""
        prices = [c["price"] for c in competitors]
        avg_price = sum(prices) / len(prices)
        min_price_market = min(prices)
        max_price_market = max(prices)

        # Preço sugerido: média - desconto competitivo
        suggested = avg_price * (1 - self.COMPETITIVE_DISCOUNT)

        # Garantir margem mínima se custo disponível
        if cost and cost > 0:
            floor_price = cost * (1 + min_margin)
            if suggested < floor_price:
                suggested = floor_price
                strategy = "cost_floor"
            else:
                strategy = "competitive"
            actual_margin = (suggested - cost) / cost if cost > 0 else 0
        else:
            strategy = "competitive"
            actual_margin = margin

        # Limites de preço
        min_allowed = cost * (1 + min_margin) if cost and cost > 0 else min_price_market * 0.8
        max_allowed = max_price_market * 1.1

        suggested = round(suggested, 2)

        logger.info(
            f"Preço competitivo calculado: R$ {suggested:.2f}",
            extra={"extra_data": {
                "avg_market": avg_price,
                "competitors": len(competitors),
                "margin": actual_margin,
            }},
        )

        return PricingResult(
            suggested_price=suggested,
            min_price=round(min_allowed, 2),
            max_price=round(max_allowed, 2),
            strategy=strategy,
            competitors_count=len(competitors),
            margin_percent=round(actual_margin * 100, 1),
            currency=currency,
            breakdown={
                "avg_market_price": round(avg_price, 2),
                "min_market_price": round(min_price_market, 2),
                "max_market_price": round(max_price_market, 2),
                "competitive_discount": f"{self.COMPETITIVE_DISCOUNT * 100}%",
                "cost": cost,
            },
        )

    def _cost_plus_pricing(
        self, cost: float, margin: float, currency: str
    ) -> PricingResult:
        """Calcula preço baseado em custo + margem."""
        suggested = cost * (1 + margin)

        logger.info(
            f"Preço custo+margem: R$ {suggested:.2f} (margem {margin * 100}%)",
            extra={"extra_data": {"cost": cost, "margin": margin}},
        )

        return PricingResult(
            suggested_price=round(suggested, 2),
            min_price=round(cost * (1 + self.MIN_MARGIN), 2),
            max_price=round(cost * (1 + margin * 2), 2),
            strategy="cost_plus",
            competitors_count=0,
            margin_percent=round(margin * 100, 1),
            currency=currency,
            breakdown={
                "cost": cost,
                "margin_applied": f"{margin * 100}%",
                "formula": f"{cost} × (1 + {margin}) = {suggested:.2f}",
            },
        )


# Singleton
_pricing_service: Optional[PricingService] = None


def get_pricing_service() -> PricingService:
    """Factory singleton."""
    global _pricing_service
    if _pricing_service is None:
        _pricing_service = PricingService()
    return _pricing_service
