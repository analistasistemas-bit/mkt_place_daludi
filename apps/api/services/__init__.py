"""
Services package — Pipeline GTIN e serviços auxiliares.

Ordem obrigatória do pipeline: rules → templates → cache → vector reuse → AI.
"""

from apps.api.services.compliance_rules import ComplianceRules, get_compliance_rules
from apps.api.services.gs1_service import GS1Service, get_gs1_service
from apps.api.services.identity_resolver import IdentityResolver, get_identity_resolver
from apps.api.services.listing_builder import ListingBuilder, get_listing_builder
from apps.api.services.llm_service import LLMService, get_llm_service
from apps.api.services.ml_service import MLService, get_ml_service
from apps.api.services.normalizer import Normalizer, get_normalizer
from apps.api.services.pipeline import Pipeline, get_pipeline
from apps.api.services.pricing import PricingService, get_pricing_service
from apps.api.services.template_renderer import TemplateRenderer, get_template_renderer
from apps.api.services.vector_service import VectorService, get_vector_service

__all__ = [
    "ComplianceRules", "get_compliance_rules",
    "GS1Service", "get_gs1_service",
    "IdentityResolver", "get_identity_resolver",
    "ListingBuilder", "get_listing_builder",
    "LLMService", "get_llm_service",
    "MLService", "get_ml_service",
    "Normalizer", "get_normalizer",
    "Pipeline", "get_pipeline",
    "PricingService", "get_pricing_service",
    "TemplateRenderer", "get_template_renderer",
    "VectorService", "get_vector_service",
]
