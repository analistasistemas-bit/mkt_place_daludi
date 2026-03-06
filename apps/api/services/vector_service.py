"""
Vector Service — Embeddings e busca por similaridade via pgvector.
Stub funcional: interface pronta para pgvector do Supabase.
"""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.vector")

EMBEDDING_DIMENSION = 1536  # OpenAI text-embedding-3-small
STUB_DIMENSION = 128  # Dimensão menor para stubs (performance local)


@dataclass
class SimilarCopy:
    """Copy similar encontrada via busca vetorial."""
    id: str
    content: str
    category: str
    similarity: float  # 0.0 - 1.0
    metadata: Dict[str, Any]


class VectorService:
    """
    Serviço de embeddings e busca vetorial via pgvector (Supabase).
    
    Fluxo do pipeline:
    1. Antes de chamar LLM, buscar copies similares aprovadas
    2. Se similaridade >= threshold → reutilizar (sem custo de IA)
    3. Após aprovação humana → salvar copy no vetor
    
    STUB: Simula embeddings e similaridade com dados determinísticos.
    PRODUÇÃO: Usar OpenAI embeddings + pgvector <-> operator.
    """

    SIMILARITY_THRESHOLD = 0.85  # Mínimo para reuso

    def __init__(
        self,
        provider: str = "stub",
        api_key: Optional[str] = None,
        supabase_client: Optional[Any] = None,
    ):
        self._provider = provider
        self._api_key = api_key
        self._supabase = supabase_client
        self._embedding_cache: Dict[str, List[float]] = {}
        self._stored_copies: List[Dict[str, Any]] = []

    async def embed_text(self, text: str) -> List[float]:
        """
        Gera embedding para texto.
        
        STUB: Gera vetor determinístico baseado no hash do texto.
        PRODUÇÃO: Chamar OpenAI embeddings API.
        """
        cache_key = hashlib.md5(text.encode()).hexdigest()

        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        # STUB: gerar embedding determinístico
        embedding = self._stub_embedding(text)
        self._embedding_cache[cache_key] = embedding

        logger.info(
            "Embedding gerado (stub)",
            extra={"extra_data": {"text_len": len(text), "dim": len(embedding)}},
        )

        return embedding

    async def find_similar_copies(
        self,
        text: str,
        category: Optional[str] = None,
        tenant_id: Optional[str] = None,
        limit: int = 5,
        min_similarity: Optional[float] = None,
    ) -> List[SimilarCopy]:
        """
        Busca copies similares aprovadas via pgvector.
        
        STUB: Retorna matches simulados das copies armazenadas localmente.
        PRODUÇÃO: Query pgvector com <-> operator no Supabase.
        
        ```sql
        -- Query real:
        SELECT id, content, category, metadata,
               1 - (embedding <-> $1) AS similarity
        FROM vector_embeddings
        WHERE tenant_id = $2
          AND category = $3
          AND 1 - (embedding <-> $1) >= $4
        ORDER BY embedding <-> $1
        LIMIT $5;
        ```
        """
        threshold = min_similarity or self.SIMILARITY_THRESHOLD

        logger.info(
            "Buscando copies similares (stub)",
            extra={"extra_data": {
                "category": category,
                "tenant_id": tenant_id,
                "threshold": threshold,
            }},
        )

        # STUB: buscar nas copies armazenadas localmente
        results = []
        for copy in self._stored_copies:
            if category and copy.get("category") != category:
                continue
            if tenant_id and copy.get("tenant_id") != tenant_id:
                continue

            # Simular similaridade
            similarity = self._stub_similarity(text, copy.get("content", ""))
            if similarity >= threshold:
                results.append(SimilarCopy(
                    id=copy.get("id", ""),
                    content=copy.get("content", ""),
                    category=copy.get("category", ""),
                    similarity=similarity,
                    metadata=copy.get("metadata", {}),
                ))

        # Ordenar por similaridade
        results.sort(key=lambda x: x.similarity, reverse=True)
        return results[:limit]

    async def save_approved_copy(
        self,
        content: str,
        category: str,
        tenant_id: str,
        listing_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Salva copy aprovada com embedding para reuso futuro.
        
        STUB: Armazena localmente.
        PRODUÇÃO: INSERT no Supabase vector_embeddings com embedding real.
        """
        embedding = await self.embed_text(content)
        copy_id = hashlib.md5(f"{tenant_id}:{content}".encode()).hexdigest()[:16]

        copy_data = {
            "id": copy_id,
            "content": content,
            "category": category,
            "tenant_id": tenant_id,
            "listing_id": listing_id,
            "embedding": embedding,
            "metadata": metadata or {},
        }

        self._stored_copies.append(copy_data)

        logger.info(
            "Copy aprovada salva (stub)",
            extra={"extra_data": {
                "copy_id": copy_id,
                "category": category,
                "tenant_id": tenant_id,
            }},
        )

        return copy_id

    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do serviço vetorial."""
        return {
            "provider": self._provider,
            "embedding_dimension": EMBEDDING_DIMENSION,
            "cached_embeddings": len(self._embedding_cache),
            "stored_copies": len(self._stored_copies),
            "similarity_threshold": self.SIMILARITY_THRESHOLD,
        }

    # ── Stubs determinísticos ──────────────────────────────────

    def _stub_embedding(self, text: str) -> List[float]:
        """Gera embedding determinístico baseado em hash."""
        seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
        rng = random.Random(seed)
        return [rng.gauss(0, 1) for _ in range(STUB_DIMENSION)]

    def _stub_similarity(self, text_a: str, text_b: str) -> float:
        """Calcula similaridade stub entre dois textos."""
        words_a = set(text_a.lower().split())
        words_b = set(text_b.lower().split())
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union) if union else 0.0


# Singleton
_vector_service: Optional[VectorService] = None


def get_vector_service() -> VectorService:
    """Factory singleton para VectorService."""
    global _vector_service
    if _vector_service is None:
        _vector_service = VectorService()
    return _vector_service
