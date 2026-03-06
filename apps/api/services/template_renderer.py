"""
Template Renderer — Renderização de copy por categoria (mín. 3: eletrônicos, casa, beleza).
Templates versionados, com fallback para built-in se não encontrar no banco.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.template_renderer")


# ============================================================
# Templates built-in por categoria (fallback)
# ============================================================

BUILTIN_TEMPLATES: Dict[str, Dict[str, Any]] = {
    "eletronicos": {
        "name": "Eletrônicos - Built-in v1",
        "version": 1,
        "title_template": "{brand} {title} - {key_feature} | {condition}",
        "description_template": """## {title}

**Marca:** {brand}
**Modelo:** {model}
**Condição:** {condition}

### Características Principais
{features}

### Especificações Técnicas
{specifications}

### O que está incluso
{included_items}

---
✅ Produto com garantia
📦 Envio rápido
🔒 Compra segura""",
        "variables": [
            "brand", "title", "key_feature", "condition", "model",
            "features", "specifications", "included_items",
        ],
    },

    "casa": {
        "name": "Casa e Decoração - Built-in v1",
        "version": 1,
        "title_template": "{brand} {title} - {material} {dimensions} | {style}",
        "description_template": """## {title}

**Marca:** {brand}
**Material:** {material}
**Dimensões:** {dimensions}
**Estilo:** {style}

### Descrição
{description}

### Características
{features}

### Cuidados
{care_instructions}

---
🏠 Transforme seu ambiente
📦 Embalagem segura
🚚 Envio para todo o Brasil""",
        "variables": [
            "brand", "title", "material", "dimensions", "style",
            "description", "features", "care_instructions",
        ],
    },

    "beleza": {
        "name": "Beleza e Cuidados - Built-in v1",
        "version": 1,
        "title_template": "{brand} {title} {volume} - {benefit}",
        "description_template": """## {title}

**Marca:** {brand}
**Volume/Quantidade:** {volume}
**Tipo de Pele/Cabelo:** {skin_type}

### Benefícios
{benefits}

### Modo de Uso
{usage_instructions}

### Ingredientes Principais
{key_ingredients}

### Informações Importantes
{warnings}

---
💄 Produto original
📋 Registro ANVISA: {anvisa_registry}
📦 Embalagem lacrada""",
        "variables": [
            "brand", "title", "volume", "benefit", "skin_type",
            "benefits", "usage_instructions", "key_ingredients",
            "warnings", "anvisa_registry",
        ],
    },
}

# Mapeamento de categorias alternativas para as 3 built-in
CATEGORY_ALIASES: Dict[str, str] = {
    "eletronicos": "eletronicos",
    "electronics": "eletronicos",
    "celulares": "eletronicos",
    "computadores": "eletronicos",
    "audio": "eletronicos",
    "video": "eletronicos",
    "informatica": "eletronicos",
    "casa": "casa",
    "home": "casa",
    "moveis": "casa",
    "decoracao": "casa",
    "cozinha": "casa",
    "jardim": "casa",
    "beleza": "beleza",
    "beauty": "beleza",
    "cosmeticos": "beleza",
    "perfumaria": "beleza",
    "saude": "beleza",
    "higiene": "beleza",
}


class TemplateRenderer:
    """
    Renderiza copy de anúncio usando template da categoria.
    
    Fluxo:
    1. Buscar template no banco (copy_templates) por tenant + categoria
    2. Se não encontrar → usar template global do banco
    3. Se não encontrar → usar template built-in
    4. Renderizar com variáveis do produto
    
    Regra: Templates são 100% determinísticos. IA não participa aqui.
    """

    def __init__(self, supabase_client: Optional[Any] = None):
        self._supabase = supabase_client

    async def render(
        self,
        product: Dict[str, Any],
        category: Optional[str] = None,
        tenant_id: Optional[str] = None,
        template_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, str]:
        """
        Renderiza título e descrição do anúncio.
        
        Retorna:
            {"title": "...", "description": "...", "template_used": "...", "template_version": 1}
        """
        # Determinar categoria normalizada
        raw_category = category or product.get("category", "geral")
        normalized_category = CATEGORY_ALIASES.get(
            raw_category.lower().replace(" ", "").replace("_", ""),
            raw_category.lower(),
        )

        # Obter template
        template = template_override or await self._get_template(
            normalized_category, tenant_id
        )

        # Preparar variáveis
        variables = self._prepare_variables(product)

        # Renderizar
        title = self._render_template(template["title_template"], variables)
        description = self._render_template(template["description_template"], variables)

        # Limpar placeholders não preenchidos
        title = self._clean_unfilled(title)
        description = self._clean_unfilled(description)

        logger.info(
            "Template renderizado",
            extra={"extra_data": {
                "category": normalized_category,
                "template": template.get("name", "unknown"),
                "gtin": product.get("gtin"),
            }},
        )

        return {
            "title": title.strip(),
            "description": description.strip(),
            "template_used": template.get("name", "unknown"),
            "template_version": template.get("version", 1),
            "category": normalized_category,
        }

    async def _get_template(
        self, category: str, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Busca template: tenant → global → built-in."""

        # 1. Buscar no banco (se disponível)
        if self._supabase and tenant_id:
            try:
                result = (
                    self._supabase.table("copy_templates")
                    .select("*")
                    .eq("category", category)
                    .eq("is_active", True)
                    .or_(f"tenant_id.eq.{tenant_id},is_global.eq.true")
                    .order("is_global", desc=False)  # Tenant-specific primeiro
                    .order("version", desc=True)
                    .limit(1)
                    .execute()
                )
                if result and result.data:
                    return result.data[0]
            except Exception as e:
                logger.warning(f"Erro ao buscar template no banco: {e}")

        # 2. Fallback: templates built-in
        if category in BUILTIN_TEMPLATES:
            return BUILTIN_TEMPLATES[category]

        # 3. Fallback final: template genérico de eletrônicos
        logger.warning(
            f"Categoria '{category}' sem template, usando eletrônicos",
            extra={"extra_data": {"category": category}},
        )
        return BUILTIN_TEMPLATES["eletronicos"]

    def _prepare_variables(self, product: Dict[str, Any]) -> Dict[str, str]:
        """Prepara variáveis do produto para o template."""
        attrs = product.get("attributes", {})

        variables: Dict[str, str] = {
            "brand": product.get("brand", ""),
            "title": product.get("title", ""),
            "model": attrs.get("model", attrs.get("modelo", "")),
            "condition": attrs.get("condition", "Novo"),
            "description": product.get("description", ""),
            # Eletrônicos
            "key_feature": attrs.get("key_feature", attrs.get("destaque", "")),
            "features": self._format_list(attrs.get("features", attrs.get("caracteristicas", []))),
            "specifications": self._format_dict(attrs.get("specifications", attrs.get("especificacoes", {}))),
            "included_items": self._format_list(attrs.get("included_items", attrs.get("itens_inclusos", []))),
            # Casa
            "material": attrs.get("material", ""),
            "dimensions": attrs.get("dimensions", attrs.get("dimensoes", "")),
            "style": attrs.get("style", attrs.get("estilo", "")),
            "care_instructions": attrs.get("care_instructions", attrs.get("cuidados", "")),
            # Beleza
            "volume": attrs.get("volume", attrs.get("quantidade", "")),
            "benefit": attrs.get("benefit", attrs.get("beneficio", "")),
            "skin_type": attrs.get("skin_type", attrs.get("tipo_pele", "")),
            "benefits": self._format_list(attrs.get("benefits", attrs.get("beneficios", []))),
            "usage_instructions": attrs.get("usage_instructions", attrs.get("modo_uso", "")),
            "key_ingredients": self._format_list(attrs.get("key_ingredients", attrs.get("ingredientes", []))),
            "warnings": attrs.get("warnings", attrs.get("avisos", "")),
            "anvisa_registry": attrs.get("anvisa_registry", attrs.get("anvisa", "N/A")),
        }

        return {k: str(v) for k, v in variables.items()}

    def _render_template(self, template: str, variables: Dict[str, str]) -> str:
        """Renderiza template substituindo {variável} por valor."""
        result = template
        for key, value in variables.items():
            result = result.replace("{" + key + "}", value)
        return result

    def _clean_unfilled(self, text: str) -> str:
        """Remove placeholders não preenchidos e linhas vazias resultantes."""
        # Remover {variavel} não preenchidas
        text = re.sub(r"\{[a-zA-Z_]+\}", "", text)
        # Remover linhas com apenas ** **
        text = re.sub(r"\*\*[^*]+:\*\*\s*\n", "", text)
        # Remover linhas vazias duplicadas
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text

    def _format_list(self, items: Any) -> str:
        """Formata lista como bullets."""
        if isinstance(items, list):
            return "\n".join(f"- {item}" for item in items if item)
        if isinstance(items, str):
            return items
        return ""

    def _format_dict(self, data: Any) -> str:
        """Formata dicionário como tabela markdown."""
        if isinstance(data, dict):
            return "\n".join(f"- **{k}:** {v}" for k, v in data.items() if v)
        if isinstance(data, str):
            return data
        return ""


# Singleton
_template_renderer: Optional[TemplateRenderer] = None


def get_template_renderer() -> TemplateRenderer:
    """Factory singleton."""
    global _template_renderer
    if _template_renderer is None:
        _template_renderer = TemplateRenderer()
    return _template_renderer
