import asyncio
import os
import sys

# Adicionar o diretório atual ao path para importar os módulos locais
sys.path.append(os.getcwd())

from apps.api.services.enrichment_service import EnrichmentService

async def main():
    service = EnrichmentService()
    # EAN-13 da Coca-Cola Lata 350ml (Brasil)
    gtin = "7894900011517"
    
    print(f"--- 🔍 Iniciando Busca Real para GTIN: {gtin} ---")
    
    # Vamos rodar a busca real na internet
    result = await service.search_product_on_internet(gtin)
    
    if result:
        print(f"\n✅ SUCESSO NO GOOGLE ENRICHMENT!")
        print(f"Fonte: {result['attributes']['raw_source']}")
        print(f"Título Identificado: {result['title']}")
        print(f"Confiança: {result['confidence']}")
    else:
        print(f"\n❌ FALHA: Google bloqueou ou não encontrou o item.")

if __name__ == "__main__":
    asyncio.run(main())
