-- ============================================================
-- MARKETPLACE SAAS — SCHEMA COMPLETO
-- Projeto: mkt_place_ia (Supabase)
-- Fase 1 — Base
-- ============================================================

-- Habilitar extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- 1. TENANTS — Organizações multi-tenant
-- ============================================================
CREATE TABLE tenants (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL UNIQUE,
    plan            TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'starter', 'pro', 'enterprise')),
    quota_products  INTEGER NOT NULL DEFAULT 100,
    quota_listings  INTEGER NOT NULL DEFAULT 50,
    quota_llm_calls INTEGER NOT NULL DEFAULT 500,
    settings        JSONB NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tenants_slug ON tenants(slug);
CREATE INDEX idx_tenants_is_active ON tenants(is_active);

-- ============================================================
-- 2. PROFILES — Extensão do Supabase Auth users
-- ============================================================
CREATE TABLE profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    full_name       TEXT,
    role            TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'admin', 'member', 'viewer')),
    avatar_url      TEXT,
    settings        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_profiles_tenant ON profiles(tenant_id);

-- ============================================================
-- 3. PRODUCTS — Produtos resolvidos via GTIN
-- ============================================================
CREATE TABLE products (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    gtin            TEXT NOT NULL,
    sku             TEXT,
    title           TEXT,
    brand           TEXT,
    category        TEXT,
    description     TEXT,
    attributes      JSONB NOT NULL DEFAULT '{}',
    images          JSONB NOT NULL DEFAULT '[]',
    cost            NUMERIC(12, 2),
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'resolved', 'needs_review', 'blocked')),
    confidence      NUMERIC(3, 2) DEFAULT 0.00,
    resolved_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, gtin)
);

CREATE INDEX idx_products_tenant ON products(tenant_id);
CREATE INDEX idx_products_gtin ON products(gtin);
CREATE INDEX idx_products_status ON products(status);
CREATE INDEX idx_products_created ON products(created_at);
CREATE INDEX idx_products_tenant_status ON products(tenant_id, status);

-- ============================================================
-- 4. PRODUCT_SOURCES — Fontes de dados do produto
-- ============================================================
CREATE TABLE product_sources (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    source_type     TEXT NOT NULL CHECK (source_type IN ('gs1', 'cnp', 'verified', 'mercadolivre', 'google', 'manual')),
    source_data     JSONB NOT NULL DEFAULT '{}',
    reliability     NUMERIC(3, 2) DEFAULT 0.50,
    fetched_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_product_sources_product ON product_sources(product_id);
CREATE INDEX idx_product_sources_tenant ON product_sources(tenant_id);

-- ============================================================
-- 5. PRODUCT_EVIDENCE — Evidências coletadas
-- ============================================================
CREATE TABLE product_evidence (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id      UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    evidence_type   TEXT NOT NULL CHECK (evidence_type IN ('image', 'url', 'document', 'api_response', 'manual')),
    content         JSONB NOT NULL DEFAULT '{}',
    confidence      NUMERIC(3, 2) DEFAULT 0.50,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_product_evidence_product ON product_evidence(product_id);
CREATE INDEX idx_product_evidence_tenant ON product_evidence(tenant_id);

-- ============================================================
-- 6. LISTINGS — Anúncios gerados
-- ============================================================
CREATE TABLE listings (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id           UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    product_id          UUID NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    idempotency_key     TEXT NOT NULL,
    version             INTEGER NOT NULL DEFAULT 1,
    title               TEXT NOT NULL,
    description         TEXT NOT NULL,
    price               NUMERIC(12, 2),
    currency            TEXT NOT NULL DEFAULT 'BRL',
    category_id         TEXT,
    attributes          JSONB NOT NULL DEFAULT '{}',
    images              JSONB NOT NULL DEFAULT '[]',
    status              TEXT NOT NULL DEFAULT 'draft'
                        CHECK (status IN ('draft', 'ready', 'pending_review', 'approved', 'published', 'paused', 'error')),
    compliance_status   TEXT NOT NULL DEFAULT 'pending'
                        CHECK (compliance_status IN ('pending', 'passed', 'failed', 'rewritten')),
    compliance_issues   JSONB NOT NULL DEFAULT '[]',
    ml_item_id          TEXT,
    ml_permalink        TEXT,
    published_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, idempotency_key)
);

CREATE INDEX idx_listings_tenant ON listings(tenant_id);
CREATE INDEX idx_listings_product ON listings(product_id);
CREATE INDEX idx_listings_status ON listings(status);
CREATE INDEX idx_listings_created ON listings(created_at);
CREATE INDEX idx_listings_tenant_status ON listings(tenant_id, status);
CREATE INDEX idx_listings_ml_item ON listings(ml_item_id);

-- ============================================================
-- 7. LISTING_VERSIONS — Histórico de versões
-- ============================================================
CREATE TABLE listing_versions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    listing_id      UUID NOT NULL REFERENCES listings(id) ON DELETE CASCADE,
    version         INTEGER NOT NULL,
    title           TEXT NOT NULL,
    description     TEXT NOT NULL,
    price           NUMERIC(12, 2),
    attributes      JSONB NOT NULL DEFAULT '{}',
    images          JSONB NOT NULL DEFAULT '[]',
    change_reason   TEXT,
    created_by      UUID REFERENCES profiles(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_listing_versions_listing ON listing_versions(listing_id);
CREATE INDEX idx_listing_versions_tenant ON listing_versions(tenant_id);

-- ============================================================
-- 8. JOBS — Jobs de processamento assíncrono
-- ============================================================
CREATE TABLE jobs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    job_type        TEXT NOT NULL CHECK (job_type IN (
                        'product.import', 'product.resolve',
                        'listing.generate', 'listing.publish',
                        'discovery.scan'
                    )),
    status          TEXT NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'queued', 'processing', 'completed', 'failed', 'cancelled')),
    payload         JSONB NOT NULL DEFAULT '{}',
    result          JSONB,
    error           TEXT,
    attempts        INTEGER NOT NULL DEFAULT 0,
    max_attempts    INTEGER NOT NULL DEFAULT 3,
    idempotency_key TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, idempotency_key)
);

CREATE INDEX idx_jobs_tenant ON jobs(tenant_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_type ON jobs(job_type);
CREATE INDEX idx_jobs_created ON jobs(created_at);
CREATE INDEX idx_jobs_tenant_status ON jobs(tenant_id, status);

-- ============================================================
-- 9. JOB_EVENTS — Log estruturado dos jobs
-- ============================================================
CREATE TABLE job_events (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    job_id          UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    event_type      TEXT NOT NULL CHECK (event_type IN (
                        'created', 'queued', 'started', 'progress',
                        'completed', 'failed', 'retrying', 'cancelled'
                    )),
    message         TEXT,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_job_events_job ON job_events(job_id);
CREATE INDEX idx_job_events_tenant ON job_events(tenant_id);
CREATE INDEX idx_job_events_type ON job_events(event_type);

-- ============================================================
-- 10. COPY_TEMPLATES — Templates por categoria (versionados)
-- ============================================================
CREATE TABLE copy_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID REFERENCES tenants(id) ON DELETE CASCADE,
    category        TEXT NOT NULL,
    name            TEXT NOT NULL,
    version         INTEGER NOT NULL DEFAULT 1,
    title_template  TEXT NOT NULL,
    description_template TEXT NOT NULL,
    variables       JSONB NOT NULL DEFAULT '[]',
    is_global       BOOLEAN NOT NULL DEFAULT false,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_copy_templates_category ON copy_templates(category);
CREATE INDEX idx_copy_templates_tenant ON copy_templates(tenant_id);
CREATE INDEX idx_copy_templates_active ON copy_templates(is_active);

-- ============================================================
-- 11. VECTOR_EMBEDDINGS — Copies aprovadas (pgvector)
-- ============================================================
CREATE TABLE vector_embeddings (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    source_type     TEXT NOT NULL CHECK (source_type IN ('listing_title', 'listing_description', 'product_copy')),
    source_id       UUID NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(1536),
    metadata        JSONB NOT NULL DEFAULT '{}',
    is_approved     BOOLEAN NOT NULL DEFAULT false,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_vector_embeddings_tenant ON vector_embeddings(tenant_id);
CREATE INDEX idx_vector_embeddings_source ON vector_embeddings(source_type, source_id);
CREATE INDEX idx_vector_embeddings_approved ON vector_embeddings(is_approved);

-- ============================================================
-- 12. LLM_CACHE — Cache de chamadas LLM
-- ============================================================
CREATE TABLE llm_cache (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    cache_key       TEXT NOT NULL,
    provider        TEXT NOT NULL,
    model           TEXT NOT NULL,
    prompt_hash     TEXT NOT NULL,
    input_tokens    INTEGER NOT NULL DEFAULT 0,
    output_tokens   INTEGER NOT NULL DEFAULT 0,
    response        JSONB NOT NULL,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, cache_key)
);

CREATE INDEX idx_llm_cache_tenant ON llm_cache(tenant_id);
CREATE INDEX idx_llm_cache_key ON llm_cache(cache_key);
CREATE INDEX idx_llm_cache_expires ON llm_cache(expires_at);

-- ============================================================
-- 13. AUDIT_LOGS — Log de auditoria
-- ============================================================
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id         UUID REFERENCES profiles(id),
    action          TEXT NOT NULL,
    resource_type   TEXT NOT NULL,
    resource_id     UUID,
    old_data        JSONB,
    new_data        JSONB,
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_logs_tenant ON audit_logs(tenant_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource ON audit_logs(resource_type, resource_id);
CREATE INDEX idx_audit_logs_created ON audit_logs(created_at);

-- ============================================================
-- 14. CACHES — Cache genérico
-- ============================================================
CREATE TABLE caches (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    cache_type      TEXT NOT NULL,
    cache_key       TEXT NOT NULL,
    value           JSONB NOT NULL,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE(tenant_id, cache_type, cache_key)
);

CREATE INDEX idx_caches_tenant ON caches(tenant_id);
CREATE INDEX idx_caches_type_key ON caches(cache_type, cache_key);
CREATE INDEX idx_caches_expires ON caches(expires_at);

-- ============================================================
-- 15. OPPORTUNITIES — Discovery (stub MVP)
-- ============================================================
CREATE TABLE opportunities (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id       UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    gtin            TEXT,
    title           TEXT,
    category        TEXT,
    score           NUMERIC(5, 2) DEFAULT 0.00,
    source          TEXT DEFAULT 'manual',
    metadata        JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'new'
                    CHECK (status IN ('new', 'analyzing', 'actionable', 'dismissed')),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_opportunities_tenant ON opportunities(tenant_id);
CREATE INDEX idx_opportunities_gtin ON opportunities(gtin);
CREATE INDEX idx_opportunities_status ON opportunities(status);
CREATE INDEX idx_opportunities_score ON opportunities(score DESC);

-- ============================================================
-- FUNÇÃO: Atualizar updated_at automaticamente
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers para updated_at
CREATE TRIGGER trg_tenants_updated_at
    BEFORE UPDATE ON tenants FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_profiles_updated_at
    BEFORE UPDATE ON profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_products_updated_at
    BEFORE UPDATE ON products FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_listings_updated_at
    BEFORE UPDATE ON listings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_copy_templates_updated_at
    BEFORE UPDATE ON copy_templates FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_caches_updated_at
    BEFORE UPDATE ON caches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_opportunities_updated_at
    BEFORE UPDATE ON opportunities FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER trg_jobs_updated_at
    BEFORE UPDATE ON jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
