"""
Normalizer — Normalização determinística de atributos de produto.
Limpa HTML, padroniza unidades, title case, remove duplicatas.
"""

from __future__ import annotations

import html
import re
import unicodedata
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.normalizer")


class Normalizer:
    """
    Normalização determinística de atributos de produto.
    
    Responsabilidades:
    - Limpar HTML e entidades
    - Padronizar unidades de medida
    - Title case para nomes/marcas
    - Remover duplicatas e espaços extras
    - Normalizar encoding (NFKD → ASCII quando possível)
    """

    # Mapeamento de unidades para padronização
    UNIT_MAP = {
        # Peso
        "quilos": "kg", "quilo": "kg", "quilograma": "kg", "quilogramas": "kg",
        "gramas": "g", "grama": "g", "gr": "g",
        "miligramas": "mg", "miligrama": "mg",
        "libras": "lb", "libra": "lb",
        # Volume
        "litros": "L", "litro": "L", "lt": "L", "lts": "L",
        "mililitros": "mL", "mililitro": "mL", "ml": "mL",
        # Comprimento
        "metros": "m", "metro": "m", "mts": "m",
        "centímetros": "cm", "centimetros": "cm", "centimetro": "cm",
        "milímetros": "mm", "milimetros": "mm", "milimetro": "mm",
        "polegadas": "pol", "polegada": "pol",
        # Potência/Elétrica
        "watts": "W", "watt": "W",
        "volts": "V", "volt": "V",
        "amperes": "A", "ampere": "A",
    }

    # Palavras que devem ficar em minúscula no title case
    LOWERCASE_WORDS = {"de", "do", "da", "dos", "das", "para", "com", "sem", "por", "e", "ou", "em", "um", "uma", "o", "a", "os", "as"}

    def normalize_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza todos os campos de um produto."""
        normalized = dict(product_data)

        # Normalizar campos de texto
        if "title" in normalized and normalized["title"]:
            normalized["title"] = self.normalize_title(normalized["title"])

        if "brand" in normalized and normalized["brand"]:
            normalized["brand"] = self.normalize_brand(normalized["brand"])

        if "description" in normalized and normalized["description"]:
            normalized["description"] = self.clean_html(normalized["description"])
            normalized["description"] = self.normalize_whitespace(normalized["description"])

        if "category" in normalized and normalized["category"]:
            normalized["category"] = self.normalize_category(normalized["category"])

        # Normalizar atributos
        if "attributes" in normalized and isinstance(normalized["attributes"], dict):
            normalized["attributes"] = self.normalize_attributes(normalized["attributes"])

        # Normalizar imagens (remover duplicatas, limpar URLs)
        if "images" in normalized and isinstance(normalized["images"], list):
            normalized["images"] = self.normalize_images(normalized["images"])

        # Marcar como normalizado
        normalized["_normalized"] = True

        logger.info(
            "Produto normalizado",
            extra={"extra_data": {"gtin": product_data.get("gtin", "N/A")}},
        )

        return normalized

    def normalize_title(self, title: str) -> str:
        """Normaliza título: title case inteligente, limpa HTML, remove duplicatas."""
        title = self.clean_html(title)
        title = self.normalize_whitespace(title)
        title = self._smart_title_case(title)
        return title

    def normalize_brand(self, brand: str) -> str:
        """Normaliza marca: upper case, limite."""
        brand = self.clean_html(brand)
        brand = self.normalize_whitespace(brand)
        return brand.upper().strip()

    def normalize_category(self, category: str) -> str:
        """Normaliza categoria: lowercase, remover acentos."""
        category = self.clean_html(category)
        category = self.normalize_whitespace(category)
        category = self._remove_accents(category.lower())
        return category.replace(" ", "_")

    def normalize_attributes(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        """Normaliza atributos: padronizar unidades, limpar valores."""
        normalized = {}
        for key, value in attrs.items():
            clean_key = self.normalize_whitespace(key.lower().strip())
            if isinstance(value, str):
                clean_value = self.clean_html(value)
                clean_value = self.normalize_whitespace(clean_value)
                clean_value = self.normalize_units(clean_value)
                normalized[clean_key] = clean_value
            else:
                normalized[clean_key] = value
        return normalized

    def normalize_images(self, images: List[str]) -> List[str]:
        """Remove duplicatas e URLs inválidas."""
        seen = set()
        unique = []
        for url in images:
            url = url.strip()
            if url and url not in seen and url.startswith(("http://", "https://")):
                seen.add(url)
                unique.append(url)
        return unique

    def clean_html(self, text: str) -> str:
        """Remove tags HTML e decodifica entidades."""
        text = html.unescape(text)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"&\w+;", " ", text)
        return text.strip()

    def normalize_whitespace(self, text: str) -> str:
        """Remove espaços extras e normaliza quebras de linha."""
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def normalize_units(self, text: str) -> str:
        """Padroniza unidades de medida."""
        for long_form, short_form in self.UNIT_MAP.items():
            pattern = rf"\b{re.escape(long_form)}\b"
            text = re.sub(pattern, short_form, text, flags=re.IGNORECASE)
        return text

    def _smart_title_case(self, text: str) -> str:
        """Title case inteligente: respeita exceções."""
        words = text.split()
        result = []
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in self.LOWERCASE_WORDS:
                result.append(word.capitalize())
            else:
                result.append(word.lower())
        return " ".join(result)

    def _remove_accents(self, text: str) -> str:
        """Remove acentos mantendo o caractere base."""
        nfkd = unicodedata.normalize("NFKD", text)
        return "".join(c for c in nfkd if not unicodedata.combining(c))


# Singleton
_normalizer: Optional[Normalizer] = None


def get_normalizer() -> Normalizer:
    """Factory singleton para Normalizer."""
    global _normalizer
    if _normalizer is None:
        _normalizer = Normalizer()
    return _normalizer
