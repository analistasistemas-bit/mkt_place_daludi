# Design: Resolução em Cascata de Produtos (OpenFoodFacts + Mercado Livre)

## Objetivo
Resolver dados de produtos importados no Daludi Marketplace utilizando fontes gratuitas em cascata, substituindo os stubs atuais do MVP.

## Abordagens Propostas

No momento, o `gs1_service.py` (`GS1Service.lookup_by_gtin`) é o serviço chamado para recuperar os dados e aplicar stubs.
Para adicionar a cascata (OpenFoodFacts -> Mercado Livre Search -> Fallback), eu proponho:

### Opção 1 (Recomendada): Evoluir e Renomear `gs1_service.py` para `product_fetch_service.py`
Como o `CLAUDE.md` define que o `gs1_service` é um "adaptável/placeholder" e a busca envolve agora OpenFoodFacts e Mercado Livre (ferramentas distintas), proponho:
1. Renomear `apps/api/services/gs1_service.py` para `apps/api/services/product_fetch_service.py` e nele implementar uma classe com 3 passos em `lookup_by_gtin`:
   - Nível 1: Chamar a API OpenFoodFacts (usando httpx, url `/api/v2/product/{gtin}.json`). Extrai nome, marcas, etc. Confidence = 70%.
   - Nível 2: Se vazio, chamar Mercado Livre Search (usando httpx, `/sites/MLB/search?q={gtin}`). Confidence = 50%.
   - Nível 3: Falha. Retorno vazio. Confidence = 14%.
2. Retornar um modelo que se alinhe ao schema `ProductResolved` (`name`, `brand`, `category`, `description`, `attributes`, `image_url`, `confidence_score`, `source`).

**Prós**: Mantém a arquitetura do MVP simples e centraliza a busca de dados externos em um só lugar já testável.
**Contras**: Exige atualizar os imports no worker (ou backend em geral) que chama o antigo `gs1_service`.

### Opção 2: Adicionar um `CascadingResolverService` Orquestrador
Deixar `gs1_service` como está (ou ignorá-lo) e criar um novo serviço em `apps/api/services/cascading_resolver.py`. Esse código faria o pipeline orquestrando adapters específicos caso os outros falhassem.
**Prós**: Segue Princípio de Responsabilidade Única (SRP) estritamente.
**Contras**: Overengineering para a fase de MVP atual. Muitos arquivos a mais.

---
**Eu recomendo seguir a Opção 1**, pois é pragmático, mantém as requisições em uma única classe de adaptação para o MVP e renomeia algo inicialmente mal denominado (não é apenas GS1). Qual você prefere que eu siga?
