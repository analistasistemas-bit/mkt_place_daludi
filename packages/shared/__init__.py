"""
Pacote shared — Schemas, configuração e utilitários compartilhados.
"""

from packages.shared.config import Settings, get_settings
from packages.shared.schemas import (
    DiscoveryOpportunity,
    Job,
    JobEvent,
    ListingDraft,
    ListingReady,
    ProductResolved,
)

__all__ = [
    "Settings",
    "get_settings",
    "ProductResolved",
    "ListingDraft",
    "ListingReady",
    "Job",
    "JobEvent",
    "DiscoveryOpportunity",
]
