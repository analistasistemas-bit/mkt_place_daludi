"""
Compliance Rules — Validação de compliance com regex e termos proibidos.
Marca spans para reescrita pelo LLM (ÚNICO ponto onde LLM é chamado para compliance).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from packages.shared.logging import get_logger

logger = get_logger("service.compliance")


@dataclass
class ComplianceSpan:
    """Span de texto que viola compliance."""
    text: str
    reason: str
    category: str       # "prohibited_term" | "misleading_claim" | "health_claim" | "legal_risk"
    severity: str       # "high" | "medium" | "low"
    start_pos: int
    end_pos: int


@dataclass
class ComplianceResult:
    """Resultado da verificação de compliance."""
    passed: bool
    status: str         # "passed" | "failed" | "rewritten"
    spans: List[ComplianceSpan] = field(default_factory=list)
    issues_count: int = 0
    high_severity_count: int = 0
    details: Dict[str, Any] = field(default_factory=dict)


# ============================================================
# Termos proibidos e regras (Mercado Livre + PROCON + ANVISA)
# ============================================================

PROHIBITED_TERMS: Dict[str, Dict[str, str]] = {
    # Alegações de saúde proibidas
    "cura": {"reason": "Alegação de cura é proibida (ANVISA)", "category": "health_claim", "severity": "high"},
    "curar": {"reason": "Alegação de cura é proibida (ANVISA)", "category": "health_claim", "severity": "high"},
    "milagroso": {"reason": "Alegação exagerada", "category": "misleading_claim", "severity": "high"},
    "milagre": {"reason": "Alegação exagerada", "category": "misleading_claim", "severity": "high"},
    "perda de peso garantida": {"reason": "Promessa de resultado sem comprovação", "category": "health_claim", "severity": "high"},
    "emagrece rápido": {"reason": "Promessa de resultado sem comprovação", "category": "health_claim", "severity": "high"},
    "sem efeitos colaterais": {"reason": "Alegação médica sem comprovação", "category": "health_claim", "severity": "high"},
    "aprovado pela anvisa": {"reason": "Alegação regulatória sem verificação", "category": "legal_risk", "severity": "high"},

    # Alegações comerciais enganosas
    "melhor do mercado": {"reason": "Superioridade não comprovada", "category": "misleading_claim", "severity": "medium"},
    "o mais barato": {"reason": "Comparação de preço não verificável", "category": "misleading_claim", "severity": "medium"},
    "garantia vitalícia": {"reason": "Garantia deve ser especificada conforme fabricante", "category": "legal_risk", "severity": "medium"},
    "inquebrável": {"reason": "Alegação de durabilidade exagerada", "category": "misleading_claim", "severity": "medium"},
    "indestrutível": {"reason": "Alegação de durabilidade exagerada", "category": "misleading_claim", "severity": "medium"},
    "à prova de tudo": {"reason": "Alegação vaga e não verificável", "category": "misleading_claim", "severity": "medium"},

    # Termos proibidos no Mercado Livre
    "réplica": {"reason": "Venda de réplicas proibida no ML", "category": "prohibited_term", "severity": "high"},
    "replica": {"reason": "Venda de réplicas proibida no ML", "category": "prohibited_term", "severity": "high"},
    "primeira linha": {"reason": "Sugere réplica", "category": "prohibited_term", "severity": "high"},
    "1a linha": {"reason": "Sugere réplica", "category": "prohibited_term", "severity": "high"},
    "1ª linha": {"reason": "Sugere réplica", "category": "prohibited_term", "severity": "high"},
    "aaa+": {"reason": "Sugere réplica", "category": "prohibited_term", "severity": "high"},
    "contrabando": {"reason": "Produto ilegal", "category": "prohibited_term", "severity": "high"},
    "importado sem nota": {"reason": "Produto irregular", "category": "prohibited_term", "severity": "high"},
    "whatsapp": {"reason": "Contato fora da plataforma proibido no ML", "category": "prohibited_term", "severity": "medium"},
    "zap": {"reason": "Contato fora da plataforma proibido no ML", "category": "prohibited_term", "severity": "medium"},
    "ligue para": {"reason": "Contato fora da plataforma proibido no ML", "category": "prohibited_term", "severity": "medium"},
    "chame no direct": {"reason": "Contato fora da plataforma proibido no ML", "category": "prohibited_term", "severity": "medium"},
}

# Padrões regex adicionais
REGEX_PATTERNS: List[Dict[str, str]] = [
    {
        "pattern": r"\b(?:100|cem)\s*%\s*(?:original|genuíno|genuino|verdadeiro)\b",
        "reason": "Alegação de autenticidade deve ser comprovável",
        "category": "misleading_claim",
        "severity": "low",
    },
    {
        "pattern": r"\b(?:grátis|free|de graça|brinde)\b(?!.*frete)",
        "reason": "Termos 'grátis' podem ser enganosos conforme PROCON",
        "category": "misleading_claim",
        "severity": "low",
    },
    {
        "pattern": r"(?:telefone|tel|fone|celular)\s*[:\-]?\s*\(?\d{2}\)?\s*\d{4,5}[\-\s]?\d{4}",
        "reason": "Número de telefone no anúncio proibido no ML",
        "category": "prohibited_term",
        "severity": "high",
    },
    {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "reason": "E-mail no anúncio proibido no ML",
        "category": "prohibited_term",
        "severity": "high",
    },
    {
        "pattern": r"(?:https?://|www\.)\S+",
        "reason": "Links externos proibidos no anúncio ML",
        "category": "prohibited_term",
        "severity": "medium",
    },
]


class ComplianceRules:
    """
    Verifica compliance de título e descrição de anúncio.
    
    Fluxo:
    1. Verificar termos proibidos (regex + lista)
    2. Marcar spans com razão e severidade
    3. Se spans encontrados → retornar para reescrita pelo LLM
    4. Se sem spans → passed
    
    REGRA: compliance_rules marca os spans, mas a reescrita é feita pelo llm_service.
    """

    def check(
        self,
        title: str,
        description: str,
        category: Optional[str] = None,
    ) -> ComplianceResult:
        """
        Verifica título e descrição contra regras de compliance.
        """
        spans: List[ComplianceSpan] = []

        # Verificar termos proibidos
        spans.extend(self._check_prohibited_terms(title, prefix_offset=0))
        spans.extend(self._check_prohibited_terms(description, prefix_offset=len(title) + 1))

        # Verificar padrões regex
        spans.extend(self._check_regex_patterns(title, prefix_offset=0))
        spans.extend(self._check_regex_patterns(description, prefix_offset=len(title) + 1))

        # Verificações específicas do título
        spans.extend(self._check_title_rules(title))

        high_count = sum(1 for s in spans if s.severity == "high")
        passed = len(spans) == 0

        result = ComplianceResult(
            passed=passed,
            status="passed" if passed else "failed",
            spans=spans,
            issues_count=len(spans),
            high_severity_count=high_count,
            details={
                "title_length": len(title),
                "description_length": len(description),
                "category": category,
            },
        )

        logger.info(
            f"Compliance {'OK' if passed else f'FALHOU ({len(spans)} issues)'}",
            extra={"extra_data": {
                "passed": passed,
                "issues": len(spans),
                "high_severity": high_count,
                "category": category,
            }},
        )

        return result

    def _check_prohibited_terms(
        self, text: str, prefix_offset: int = 0
    ) -> List[ComplianceSpan]:
        """Verifica termos proibidos no texto."""
        spans = []
        text_lower = text.lower()

        for term, info in PROHIBITED_TERMS.items():
            idx = 0
            while True:
                pos = text_lower.find(term, idx)
                if pos == -1:
                    break
                spans.append(ComplianceSpan(
                    text=text[pos:pos + len(term)],
                    reason=info["reason"],
                    category=info["category"],
                    severity=info["severity"],
                    start_pos=prefix_offset + pos,
                    end_pos=prefix_offset + pos + len(term),
                ))
                idx = pos + len(term)

        return spans

    def _check_regex_patterns(
        self, text: str, prefix_offset: int = 0
    ) -> List[ComplianceSpan]:
        """Verifica padrões regex no texto."""
        spans = []

        for rule in REGEX_PATTERNS:
            for match in re.finditer(rule["pattern"], text, re.IGNORECASE):
                spans.append(ComplianceSpan(
                    text=match.group(),
                    reason=rule["reason"],
                    category=rule["category"],
                    severity=rule["severity"],
                    start_pos=prefix_offset + match.start(),
                    end_pos=prefix_offset + match.end(),
                ))

        return spans

    def _check_title_rules(self, title: str) -> List[ComplianceSpan]:
        """Regras específicas para o título do anúncio."""
        spans = []

        # Título muito longo (ML limita a 60)
        if len(title) > 60:
            spans.append(ComplianceSpan(
                text=title[60:],
                reason=f"Título excede 60 caracteres ({len(title)} chars). ML truncará.",
                category="legal_risk",
                severity="low",
                start_pos=60,
                end_pos=len(title),
            ))

        # Título todo em MAIÚSCULAS (proibido no ML)
        if title.isupper() and len(title) > 5:
            spans.append(ComplianceSpan(
                text=title,
                reason="Título todo em maiúsculas é proibido no ML",
                category="prohibited_term",
                severity="medium",
                start_pos=0,
                end_pos=len(title),
            ))

        # Emojis no título
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "]+",
            flags=re.UNICODE,
        )
        for match in emoji_pattern.finditer(title):
            spans.append(ComplianceSpan(
                text=match.group(),
                reason="Emojis no título não são recomendados no ML",
                category="misleading_claim",
                severity="low",
                start_pos=match.start(),
                end_pos=match.end(),
            ))

        return spans


# Singleton
_compliance_rules: Optional[ComplianceRules] = None


def get_compliance_rules() -> ComplianceRules:
    """Factory singleton."""
    global _compliance_rules
    if _compliance_rules is None:
        _compliance_rules = ComplianceRules()
    return _compliance_rules
