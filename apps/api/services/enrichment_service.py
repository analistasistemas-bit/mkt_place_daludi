import httpx
import re
import asyncio
from typing import Dict, Any, Optional
from packages.shared.logging import get_logger

logger = get_logger("service.enrichment")

class EnrichmentService:
    """
    Serviço para busca de informações de produtos na internet (fallback final).
    Este serviço deve ser utilizado preferencialmente por Workers para evitar delay na API.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    async def search_product_on_internet(self, gtin: str) -> Optional[Dict[str, Any]]:
        """
        Realiza uma busca em múltiplos motores (DuckDuckGo, Bing, Google) e tenta extrair o título.
        """
        logger.info(f"🔍 Pesquisando internet para GTIN: {gtin}")
        
        # 1. Tentar DuckDuckGo (HTML)
        res_ddg = await self._search_ddg(gtin)
        if res_ddg:
            return res_ddg
            
        # 2. Tentar Bing
        res_bing = await self._search_bing(gtin)
        if res_bing:
            return res_bing
            
        # 3. Tentar Google (Scraping básico)
        res_google = await self._search_google(gtin)
        if res_google:
            return res_google

        return None

    async def _search_ddg(self, gtin: str) -> Optional[Dict[str, Any]]:
        url = f"https://duckduckgo.com/html/?q={gtin}"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    # Regex flexível para class="result__a" ou class='result__a'
                    matches = re.findall(r'class=["\']result__a["\'][^>]*>(.*?)</a>', response.text, re.IGNORECASE | re.DOTALL)
                    return self._process_matches(matches, gtin, "duckduckgo")
        except Exception as e:
            logger.error(f"Erro DDG: {e}")
        return None

    async def _search_bing(self, gtin: str) -> Optional[Dict[str, Any]]:
        url = f"https://www.bing.com/search?q={gtin}"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    matches = re.findall(r'<h2[^>]*><a[^>]*>(.*?)</a>', response.text, re.IGNORECASE | re.DOTALL)
                    return self._process_matches(matches, gtin, "bing")
        except Exception as e:
            logger.error(f"Erro Bing: {e}")
        return None

    async def _search_google(self, gtin: str) -> Optional[Dict[str, Any]]:
        # Google é agressivo no bloqueio, mas tentamos o básico
        url = f"https://www.google.com/search?q={gtin}&hl=pt-BR"
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url, headers=self.headers)
                if response.status_code == 200:
                    # Títulos no Google costumam estar em <h3>
                    matches = re.findall(r'<h3[^>]*>(.*?)</h3>', response.text, re.IGNORECASE | re.DOTALL)
                    return self._process_matches(matches, gtin, "google")
        except Exception as e:
            logger.error(f"Erro Google: {e}")
        return None

    def _process_matches(self, matches: list[str], gtin: str, source: str) -> Optional[Dict[str, Any]]:
        if not matches:
            return None
            
        candidates = []
        # Palavras para remover do título (marketplaces e sufixos inúteis)
        garbage = [
            "Amazon.com.br", "Mercado Livre", "eBay", "Shopee", "Magalu", "Americanas",
            "Casas Bahia", "Extra.com.br", "Ponto Frio", "AliExpress", "Cosmos", "Bluesoft",
            "Pinterest", "Youtube", "Facebook", "Instagram", " - ", " | ", " : "
        ]
        
        for m in matches[:8]:
            title = self._clean_html_tags(m)
            # Se for muito curto ou apenas o EAN, ignora
            if len(title) < 15 or title == gtin:
                continue
                
            # Limpeza agressiva: remove nomes de lojas do final
            clean_title = title
            for g in garbage:
                if g in clean_title:
                    # Remove do g em diante se estiver no final do título
                    idx = clean_title.find(g)
                    if idx > 10:
                        clean_title = clean_title[:idx].strip()
            
            # Remove caracteres estranhos que sobram no final
            clean_title = re.sub(r'(?i)[\s\-\|\:\.]+$', '', clean_title).strip()
            
            if len(clean_title) > 10:
                candidates.append(clean_title)
                
        if not candidates:
            return None
            
        # Pega o primeiro e mais longo dos 3 primeiros (heurística simples)
        best_title = max(candidates[:3], key=len)
        
        logger.info(f"✨ Identificado via {source}: {best_title}")
        
        return {
            "gtin": gtin,
            "title": best_title,
            "brand": "", # Difícil de garantir via scraping puro
            "source": "internet_search",
            "confidence": 0.45,
            "description": f"Dados obtidos via {source} para EAN {gtin}. Requer revisão.",
            "attributes": {
                "discovery_method": f"web_scraping_{source}",
                "raw_source": source
            }
        }

        return None

    def _clean_html_tags(self, text: str) -> str:
        """Remove tags HTML e entidades comuns."""
        text = re.sub(r'<[^>]+>', '', text)
        text = text.replace("&quot;", '"').replace("&amp;", "&").replace("&#39;", "'")
        return text.strip()

_enrichment_service = None

def get_enrichment_service() -> EnrichmentService:
    global _enrichment_service
    if _enrichment_service is None:
        _enrichment_service = EnrichmentService()
    return _enrichment_service
