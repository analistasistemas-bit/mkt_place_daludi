"""
LLM Service — Chamadas de IA com batching obrigatório (10-30 itens).
Stub funcional: aplica transformações determinísticas simulando LLM.
Regra: LLM é ÚLTIMO recurso, chamado apenas após compliance_rules marcar spans.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.llm")

# Limites de batching conforme CLAUDE.md
MIN_BATCH_SIZE = 10
MAX_BATCH_SIZE = 30


@dataclass
class LLMResponse:
    """Resposta de uma chamada LLM."""
    text: str
    model: str
    tokens_used: int
    cached: bool
    cost_estimate: float  # em USD


@dataclass
class ComplianceRewriteResult:
    """Resultado de reescrita de compliance span."""
    original: str
    rewritten: str
    reason: str
    confidence: float


class LLMService:
    """
    Serviço de LLM com batching obrigatório 10-30 itens.
    
    REGRA ABSOLUTA (CLAUDE.md):
    - IA NUNCA decide fatos do produto, preço ou lógica de negócio
    - IA pode: polir texto, reescrever compliance spans, comprimir títulos
    - Batching: 10-30 itens por chamada, agrupados por categoria
    - Cache agressivo: se só preço/estoque mudou → sem LLM
    
    STUB: Aplica transformações determinísticas simulando comportamento LLM.
    PRODUÇÃO: Integrar com OpenAI/Anthropic via LLM_PROVIDER.
    """

    def __init__(
        self,
        provider: str = "stub",
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
    ):
        self._provider = provider
        self._api_key = api_key
        self._model = model
        self._cache: Dict[str, str] = {}
        self._total_tokens = 0
        self._total_cost = 0.0

    async def batch_polish_listings(
        self,
        listings: List[Dict[str, Any]],
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Polimento em batch de listings (10-30 itens).
        
        Melhora fluidez e legibilidade SEM alterar fatos.
        Agrupa por categoria para consistência.
        """
        if len(listings) > MAX_BATCH_SIZE:
            logger.warning(
                f"Batch excede máximo ({len(listings)} > {MAX_BATCH_SIZE}), dividindo",
                extra={"extra_data": {"count": len(listings), "category": category}},
            )
            results = []
            for i in range(0, len(listings), MAX_BATCH_SIZE):
                chunk = listings[i:i + MAX_BATCH_SIZE]
                chunk_results = await self.batch_polish_listings(chunk, category)
                results.extend(chunk_results)
            return results

        logger.info(
            f"Polindo batch de {len(listings)} listings (stub)",
            extra={"extra_data": {"count": len(listings), "category": category}},
        )

        polished = []
        for listing in listings:
            cache_key = self._cache_key("polish", listing.get("description", ""))

            if cache_key in self._cache:
                listing["description"] = self._cache[cache_key]
                listing["_polished"] = True
                listing["_cached"] = True
            else:
                # STUB: simular polimento
                original_desc = listing.get("description", "")
                polished_desc = self._stub_polish(original_desc)
                self._cache[cache_key] = polished_desc
                listing["description"] = polished_desc
                listing["_polished"] = True
                listing["_cached"] = False
                self._total_tokens += len(original_desc.split()) * 2

            polished.append(listing)

        return polished

    async def rewrite_compliance_spans(
        self,
        spans: List[Dict[str, Any]],
    ) -> List[ComplianceRewriteResult]:
        """
        Reescreve spans marcados pelo compliance_rules.
        
        CHAMADO SOMENTE pelo compliance_rules quando encontra termos problemáticos.
        Cada span contém: text, reason, start_pos, end_pos.
        """
        logger.info(
            f"Reescrevendo {len(spans)} compliance spans (stub)",
            extra={"extra_data": {"count": len(spans)}},
        )

        results = []
        for span in spans:
            original = span.get("text", "")
            reason = span.get("reason", "termo proibido")

            # STUB: reescrita determinística
            rewritten = self._stub_rewrite_compliance(original, reason)

            results.append(ComplianceRewriteResult(
                original=original,
                rewritten=rewritten,
                reason=reason,
                confidence=0.85,
            ))

            self._total_tokens += len(original.split()) * 3

        return results

    async def compress_title(
        self, title: str, max_length: int = 60
    ) -> str:
        """
        Comprime título para caber no limite do ML (60 chars).
        
        Mantém informações essenciais: marca, modelo, atributo-chave.
        """
        if len(title) <= max_length:
            return title

        cache_key = self._cache_key("compress", title)
        if cache_key in self._cache:
            return self._cache[cache_key]

        # STUB: compressão determinística
        compressed = self._stub_compress(title, max_length)
        self._cache[cache_key] = compressed
        self._total_tokens += len(title.split()) * 2

        logger.info(
            "Título comprimido (stub)",
            extra={"extra_data": {
                "original_len": len(title),
                "compressed_len": len(compressed),
            }},
        )

        return compressed

    def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso do LLM."""
        return {
            "provider": self._provider,
            "model": self._model,
            "total_tokens": self._total_tokens,
            "total_cost_usd": self._total_cost,
            "cache_entries": len(self._cache),
        }

    # ── Stubs determinísticos ──────────────────────────────────

    def _stub_polish(self, text: str) -> str:
        """Stub: simula polimento de texto."""
        if not text:
            return text
        # Capitalizar primeira letra de cada sentença
        sentences = text.split(". ")
        polished = ". ".join(s.strip().capitalize() for s in sentences if s.strip())
        # Adicionar emoji sutil de seção
        polished = polished.replace("### ", "### ✨ ")
        return polished

    def _stub_rewrite_compliance(self, text: str, reason: str) -> str:
        """Stub: simula reescrita de compliance."""
        replacements = {
            "melhor do mercado": "excelente qualidade",
            "garantia vitalícia": "garantia conforme fabricante",
            "100% original": "produto original",
            "cura": "auxilia no tratamento",
            "milagroso": "eficiente",
            "perda de peso": "auxílio no emagrecimento",
            "sem efeitos colaterais": "consulte um profissional",
        }
        result = text
        for old, new in replacements.items():
            result = result.replace(old, new)
            result = result.replace(old.capitalize(), new.capitalize())
        return result

    def _stub_compress(self, title: str, max_length: int) -> str:
        """Stub: comprime título removendo palavras dispensáveis."""
        # Remover palavras desnecessárias
        stop_words = {"de", "do", "da", "dos", "das", "para", "com", "sem", "por", "e", "ou", "em", "um", "uma"}
        words = title.split()
        essential = [w for w in words if w.lower() not in stop_words]
        compressed = " ".join(essential)

        # Se ainda excede, truncar mantendo início
        if len(compressed) > max_length:
            compressed = compressed[:max_length - 3].rsplit(" ", 1)[0] + "..."

        return compressed

    def _cache_key(self, operation: str, text: str) -> str:
        """Gera chave de cache para texto."""
        content = f"{operation}:{text}"
        return hashlib.md5(content.encode()).hexdigest()


# Singleton
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Factory singleton para LLMService."""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
