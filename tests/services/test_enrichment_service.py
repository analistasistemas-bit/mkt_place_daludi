import pytest
from unittest.mock import AsyncMock, patch
from apps.api.services.enrichment_service import EnrichmentService

@pytest.mark.asyncio
async def test_search_product_prioritizes_google():
    """
    Testa se o serviço de enriquecimento prioriza o Google como PRIMEIRA fonte.
    Se o Google retornar dados, o DDG e Bing não devem ser chamados.
    """
    service = EnrichmentService()
    gtin = "7891234567890"
    
    # Mock do _search_google retornando sucesso de cara
    with patch.object(service, '_search_google', new_callable=AsyncMock) as mock_google:
        mock_google.return_value = {"title": "Produto Google", "source": "google"}
        
        # Mocks para espionar chamadas dos fallbacks
        with patch.object(service, '_search_ddg', new_callable=AsyncMock) as mock_ddg:
            with patch.object(service, '_search_bing', new_callable=AsyncMock) as mock_bing:
                
                result = await service.search_product_on_internet(gtin)
                
                # Deve retornar o resultado do Google
                assert result["title"] == "Produto Google"
                
                # Se a prioridade estiver certa (Google no topo), DDG e Bing NÃO devem ser chamados
                mock_google.assert_called_once()
                mock_ddg.assert_not_called()
                mock_bing.assert_not_called()
