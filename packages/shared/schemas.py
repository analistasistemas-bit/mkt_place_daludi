"""
Contratos Pydantic v2 — Fonte de verdade dos schemas do sistema.
Definidos conforme CLAUDE.md: ProductResolved, ListingDraft, ListingReady, JobEvent, DiscoveryOpportunity.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


# ============================================================
# Enums
# ============================================================

class ProductStatus(str, Enum):
    PENDING = "pending"
    RESOLVED = "resolved"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"


class ListingStatus(str, Enum):
    DRAFT = "draft"
    READY = "ready"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    PUBLISHED = "published"
    PAUSED = "paused"
    ERROR = "error"


class ComplianceStatus(str, Enum):
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REWRITTEN = "rewritten"


class JobType(str, Enum):
    PRODUCT_IMPORT = "product.import"
    PRODUCT_RESOLVE = "product.resolve"
    LISTING_GENERATE = "listing.generate"
    LISTING_PUBLISH = "listing.publish"
    DISCOVERY_SCAN = "discovery.scan"


class JobStatus(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobEventType(str, Enum):
    CREATED = "created"
    QUEUED = "queued"
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class OpportunityStatus(str, Enum):
    NEW = "new"
    ANALYZING = "analyzing"
    ACTIONABLE = "actionable"
    DISMISSED = "dismissed"


class SourceType(str, Enum):
    GS1 = "gs1"
    CNP = "cnp"
    VERIFIED = "verified"
    MERCADOLIVRE = "mercadolivre"
    GOOGLE = "google"
    MANUAL = "manual"


class UserRole(str, Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class TenantPlan(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


# ============================================================
# Base Models
# ============================================================

class BaseSchema(BaseModel):
    """Schema base com configuração compartilhada."""
    model_config = {"from_attributes": True, "str_strip_whitespace": True}


class TenantBound(BaseSchema):
    """Schema que exige tenant_id."""
    tenant_id: uuid.UUID


class TimestampMixin(BaseSchema):
    """Mixin com timestamps de criação e atualização."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================
# Tenant
# ============================================================

class TenantBase(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100)
    plan: TenantPlan = TenantPlan.FREE


class TenantCreate(TenantBase):
    pass


class Tenant(TenantBase, TimestampMixin):
    id: uuid.UUID
    quota_products: int = 100
    quota_listings: int = 50
    quota_llm_calls: int = 500
    settings: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


# ============================================================
# Profile
# ============================================================

class ProfileBase(BaseSchema):
    full_name: Optional[str] = None
    role: UserRole = UserRole.MEMBER


class ProfileCreate(ProfileBase):
    id: uuid.UUID  # auth.users id
    tenant_id: uuid.UUID


class Profile(ProfileBase, TimestampMixin):
    id: uuid.UUID
    tenant_id: uuid.UUID
    avatar_url: Optional[str] = None
    settings: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# ProductResolved (contrato obrigatório)
# ============================================================

class ProductBase(TenantBound):
    gtin: str = Field(..., min_length=8, max_length=14)
    sku: Optional[str] = None
    title: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list)
    cost: Optional[float] = None

    @field_validator("gtin")
    @classmethod
    def validate_gtin(cls, v: str) -> str:
        cleaned = v.strip().replace("-", "").replace(" ", "")
        if not cleaned.isdigit():
            raise ValueError("GTIN deve conter apenas dígitos")
        if len(cleaned) not in (8, 12, 13, 14):
            raise ValueError("GTIN deve ter 8, 12, 13 ou 14 dígitos")
        return cleaned


class ProductCreate(ProductBase):
    pass


class ProductResolved(ProductBase, TimestampMixin):
    """Contrato principal: produto resolvido via pipeline GTIN."""
    id: uuid.UUID
    status: ProductStatus = ProductStatus.PENDING
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    resolved_at: Optional[datetime] = None


# ============================================================
# ListingDraft (contrato obrigatório)
# ============================================================

class ListingBase(TenantBound):
    product_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=1)
    price: Optional[float] = None
    currency: str = "BRL"
    category_id: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    images: list[str] = Field(default_factory=list)


class ListingDraft(ListingBase, TimestampMixin):
    """Contrato: anúncio gerado pelo pipeline (draft)."""
    id: uuid.UUID
    idempotency_key: str
    version: int = 1
    status: ListingStatus = ListingStatus.DRAFT
    compliance_status: ComplianceStatus = ComplianceStatus.PENDING
    compliance_issues: list[dict[str, Any]] = Field(default_factory=list)


class ListingCreate(ListingBase):
    idempotency_key: str


# ============================================================
# ListingReady (contrato obrigatório)
# ============================================================

class ListingReady(ListingDraft):
    """Contrato: anúncio pronto para publicação (compliance OK)."""
    status: ListingStatus = ListingStatus.READY
    compliance_status: ComplianceStatus = ComplianceStatus.PASSED
    ml_item_id: Optional[str] = None
    ml_permalink: Optional[str] = None
    published_at: Optional[datetime] = None


# ============================================================
# JobEvent (contrato obrigatório)
# ============================================================

class JobBase(TenantBound):
    job_type: JobType
    payload: dict[str, Any] = Field(default_factory=dict)


class JobCreate(JobBase):
    idempotency_key: Optional[str] = None
    max_attempts: int = 3


class Job(JobBase, TimestampMixin):
    """Contrato: job de processamento assíncrono."""
    id: uuid.UUID
    status: JobStatus = JobStatus.PENDING
    result: Optional[dict[str, Any]] = None
    error: Optional[str] = None
    attempts: int = 0
    max_attempts: int = 3
    idempotency_key: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class JobEvent(BaseSchema):
    """Contrato obrigatório: evento de job com contexto completo."""
    id: uuid.UUID
    tenant_id: uuid.UUID
    job_id: uuid.UUID
    event_type: JobEventType
    message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobEventCreate(TenantBound):
    job_id: uuid.UUID
    event_type: JobEventType
    message: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ============================================================
# DiscoveryOpportunity (stub MVP)
# ============================================================

class DiscoveryOpportunityBase(TenantBound):
    gtin: Optional[str] = None
    title: Optional[str] = None
    category: Optional[str] = None
    score: float = Field(default=0.0, ge=0.0, le=100.0)
    source: str = "manual"
    metadata: dict[str, Any] = Field(default_factory=dict)


class DiscoveryOpportunity(DiscoveryOpportunityBase, TimestampMixin):
    """Contrato stub MVP: oportunidade descoberta."""
    id: uuid.UUID
    status: OpportunityStatus = OpportunityStatus.NEW


class DiscoveryOpportunityCreate(DiscoveryOpportunityBase):
    pass


# ============================================================
# Schemas auxiliares
# ============================================================

class CopyTemplate(TimestampMixin):
    """Template de copy por categoria."""
    id: uuid.UUID
    tenant_id: Optional[uuid.UUID] = None
    category: str
    name: str
    version: int = 1
    title_template: str
    description_template: str
    variables: list[str] = Field(default_factory=list)
    is_global: bool = False
    is_active: bool = True


class ProductImportRequest(BaseSchema):
    """Request para importar produtos via planilha ou lista de GTINs."""
    tenant_id: uuid.UUID
    gtins: Optional[list[str]] = None
    file_url: Optional[str] = None

    @field_validator("gtins")
    @classmethod
    def validate_gtins_list(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None and len(v) == 0:
            raise ValueError("Lista de GTINs não pode estar vazia")
        return v


class PaginationParams(BaseSchema):
    """Parâmetros de paginação."""
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.per_page


class PaginatedResponse(BaseSchema):
    """Resposta paginada genérica."""
    items: list[Any]
    total: int
    page: int
    per_page: int
    pages: int
