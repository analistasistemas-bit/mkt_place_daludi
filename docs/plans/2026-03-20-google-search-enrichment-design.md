# Design: Google Search Enrichment Fallback

Melhoria do sistema de busca externa para resolução de GTINs (EAN) utilizando o Google como fonte primária robusta antes de recorrer ao DuckDuckGo ou Bing.

## 1. Visão Geral
Atualmente, o `EnrichmentService` utiliza um scraper simples que é facilmente bloqueado pelo Google. Este design propõe uma abordagem híbrida: 
- Uso de API especializada (**Serper.dev**) se uma `SEARCH_API_KEY` estiver configurada.
- Um **Scraper Inteligente** (v2) com headers rotativos e regex resiliente como fallback imediato.

## 2. Abordagem Técnica

### 2.1 Orquestração (`search_product_on_internet`)
A cascata de busca será reordenada:
1.  **Google API** (Se `SEARCH_API_KEY` existir no `.env`).
2.  **Google Scraper v2** (Headers modernos + seletores de títulos atualizados).
3.  **DuckDuckGo** (Fallback de segurança).
4.  **Bing** (Fallback final).

### 2.2 Atributos Coletados
- **Título do Produto:** Extraído do snippet principal de resultado do Google.
- **Marca (Tentativa):** Identificada via análise de strings no título (parcial).
- **Descrição:** Mensagem informativa de "Dados obtidos via internet - requer revisão".

### 2.3 Cálculo de Confiança
Para garantir que o produto não pule a revisão humana indevidamente:
- **Score:** 0.40 a 0.45.
- **Status:** Sempre resultará em `needs_review` no `IdentityResolver`.

## 3. Segurança e Resiliência
- **Rate Limit:** Adicionar um `jitter` (atraso aleatório) se houver múltiplas buscas seguidas para evitar banimentos de IP.
- **User-Agents:** Lista rotativa de User-Agents simulando navegadores Desktop modernos (Chrome/Windows e Safari/Mac).

## 4. Plano de Verificação
- Log detalhado no Worker informando qual fonte (Google API vs Google Scraper) teve sucesso.
- Interface do Dashboard deve exibir claramente que a fonte é `internet_search`.
