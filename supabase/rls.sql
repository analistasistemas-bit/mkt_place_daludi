-- ============================================================
-- MARKETPLACE SAAS — ROW LEVEL SECURITY (RLS)
-- Todas as tabelas protegidas por tenant_id
-- ============================================================

-- ============================================================
-- Função auxiliar: extrair tenant_id do JWT ou profile
-- ============================================================
CREATE OR REPLACE FUNCTION public.get_tenant_id()
RETURNS UUID AS $$
    SELECT COALESCE(
        (current_setting('request.jwt.claims', true)::json ->> 'tenant_id')::uuid,
        (
            SELECT tenant_id FROM public.profiles
            WHERE id = auth.uid()
            LIMIT 1
        )
    );
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- ============================================================
-- TENANTS — Apenas membros do tenant podem ver seu próprio tenant
-- ============================================================
ALTER TABLE tenants ENABLE ROW LEVEL SECURITY;

CREATE POLICY "tenants_select_own"
    ON tenants FOR SELECT
    USING (id = public.get_tenant_id());

CREATE POLICY "tenants_update_own"
    ON tenants FOR UPDATE
    USING (id = public.get_tenant_id())
    WITH CHECK (id = public.get_tenant_id());

-- ============================================================
-- PROFILES
-- ============================================================
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "profiles_select_own_tenant"
    ON profiles FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "profiles_insert_own"
    ON profiles FOR INSERT
    WITH CHECK (id = auth.uid());

CREATE POLICY "profiles_update_own"
    ON profiles FOR UPDATE
    USING (id = auth.uid())
    WITH CHECK (id = auth.uid());

-- ============================================================
-- PRODUCTS
-- ============================================================
ALTER TABLE products ENABLE ROW LEVEL SECURITY;

CREATE POLICY "products_select_own_tenant"
    ON products FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "products_insert_own_tenant"
    ON products FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "products_update_own_tenant"
    ON products FOR UPDATE
    USING (tenant_id = public.get_tenant_id())
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "products_delete_own_tenant"
    ON products FOR DELETE
    USING (tenant_id = public.get_tenant_id());

-- ============================================================
-- PRODUCT_SOURCES
-- ============================================================
ALTER TABLE product_sources ENABLE ROW LEVEL SECURITY;

CREATE POLICY "product_sources_select_own_tenant"
    ON product_sources FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "product_sources_insert_own_tenant"
    ON product_sources FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "product_sources_update_own_tenant"
    ON product_sources FOR UPDATE
    USING (tenant_id = public.get_tenant_id())
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "product_sources_delete_own_tenant"
    ON product_sources FOR DELETE
    USING (tenant_id = public.get_tenant_id());

-- ============================================================
-- PRODUCT_EVIDENCE
-- ============================================================
ALTER TABLE product_evidence ENABLE ROW LEVEL SECURITY;

CREATE POLICY "product_evidence_select_own_tenant"
    ON product_evidence FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "product_evidence_insert_own_tenant"
    ON product_evidence FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "product_evidence_update_own_tenant"
    ON product_evidence FOR UPDATE
    USING (tenant_id = public.get_tenant_id())
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "product_evidence_delete_own_tenant"
    ON product_evidence FOR DELETE
    USING (tenant_id = public.get_tenant_id());

-- ============================================================
-- LISTINGS
-- ============================================================
ALTER TABLE listings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "listings_select_own_tenant"
    ON listings FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "listings_insert_own_tenant"
    ON listings FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "listings_update_own_tenant"
    ON listings FOR UPDATE
    USING (tenant_id = public.get_tenant_id())
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "listings_delete_own_tenant"
    ON listings FOR DELETE
    USING (tenant_id = public.get_tenant_id());

-- ============================================================
-- LISTING_VERSIONS
-- ============================================================
ALTER TABLE listing_versions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "listing_versions_select_own_tenant"
    ON listing_versions FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "listing_versions_insert_own_tenant"
    ON listing_versions FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

-- ============================================================
-- JOBS
-- ============================================================
ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "jobs_select_own_tenant"
    ON jobs FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "jobs_insert_own_tenant"
    ON jobs FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "jobs_update_own_tenant"
    ON jobs FOR UPDATE
    USING (tenant_id = public.get_tenant_id())
    WITH CHECK (tenant_id = public.get_tenant_id());

-- ============================================================
-- JOB_EVENTS
-- ============================================================
ALTER TABLE job_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "job_events_select_own_tenant"
    ON job_events FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "job_events_insert_own_tenant"
    ON job_events FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

-- ============================================================
-- COPY_TEMPLATES — Global templates visíveis por todos, tenant templates pelo tenant
-- ============================================================
ALTER TABLE copy_templates ENABLE ROW LEVEL SECURITY;

CREATE POLICY "copy_templates_select_global_or_own"
    ON copy_templates FOR SELECT
    USING (is_global = true OR tenant_id = public.get_tenant_id());

CREATE POLICY "copy_templates_insert_own_tenant"
    ON copy_templates FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "copy_templates_update_own_tenant"
    ON copy_templates FOR UPDATE
    USING (tenant_id = public.get_tenant_id())
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "copy_templates_delete_own_tenant"
    ON copy_templates FOR DELETE
    USING (tenant_id = public.get_tenant_id());

-- ============================================================
-- VECTOR_EMBEDDINGS
-- ============================================================
ALTER TABLE vector_embeddings ENABLE ROW LEVEL SECURITY;

CREATE POLICY "vector_embeddings_select_own_tenant"
    ON vector_embeddings FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "vector_embeddings_insert_own_tenant"
    ON vector_embeddings FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "vector_embeddings_update_own_tenant"
    ON vector_embeddings FOR UPDATE
    USING (tenant_id = public.get_tenant_id())
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "vector_embeddings_delete_own_tenant"
    ON vector_embeddings FOR DELETE
    USING (tenant_id = public.get_tenant_id());

-- ============================================================
-- LLM_CACHE
-- ============================================================
ALTER TABLE llm_cache ENABLE ROW LEVEL SECURITY;

CREATE POLICY "llm_cache_select_own_tenant"
    ON llm_cache FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "llm_cache_insert_own_tenant"
    ON llm_cache FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

CREATE POLICY "llm_cache_delete_own_tenant"
    ON llm_cache FOR DELETE
    USING (tenant_id = public.get_tenant_id());

-- ============================================================
-- AUDIT_LOGS — Apenas leitura pelo tenant
-- ============================================================
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "audit_logs_select_own_tenant"
    ON audit_logs FOR SELECT
    USING (tenant_id = public.get_tenant_id());

CREATE POLICY "audit_logs_insert_own_tenant"
    ON audit_logs FOR INSERT
    WITH CHECK (tenant_id = public.get_tenant_id());

-- ============================================================
-- CACHES
-- ============================================================
ALTER TABLE caches ENABLE ROW LEVEL SECURITY;

CREATE POLICY "caches_select_own_tenant"
    ON caches FOR SELECT
    USING (tenant_id = auth.tenant_id());

CREATE POLICY "caches_insert_own_tenant"
    ON caches FOR INSERT
    WITH CHECK (tenant_id = auth.tenant_id());

CREATE POLICY "caches_update_own_tenant"
    ON caches FOR UPDATE
    USING (tenant_id = auth.tenant_id())
    WITH CHECK (tenant_id = auth.tenant_id());

CREATE POLICY "caches_delete_own_tenant"
    ON caches FOR DELETE
    USING (tenant_id = auth.tenant_id());

-- ============================================================
-- OPPORTUNITIES
-- ============================================================
ALTER TABLE opportunities ENABLE ROW LEVEL SECURITY;

CREATE POLICY "opportunities_select_own_tenant"
    ON opportunities FOR SELECT
    USING (tenant_id = auth.tenant_id());

CREATE POLICY "opportunities_insert_own_tenant"
    ON opportunities FOR INSERT
    WITH CHECK (tenant_id = auth.tenant_id());

CREATE POLICY "opportunities_update_own_tenant"
    ON opportunities FOR UPDATE
    USING (tenant_id = auth.tenant_id())
    WITH CHECK (tenant_id = auth.tenant_id());

CREATE POLICY "opportunities_delete_own_tenant"
    ON opportunities FOR DELETE
    USING (tenant_id = auth.tenant_id());
