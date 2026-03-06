-- ============================================================
-- MARKETPLACE SAAS — SEEDS (Dados Mínimos de Teste)
-- ============================================================

-- ============================================================
-- Tenant de teste
-- ============================================================
INSERT INTO tenants (id, name, slug, plan, quota_products, quota_listings, quota_llm_calls)
VALUES (
    'a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11',
    'Empresa Teste',
    'empresa-teste',
    'pro',
    500,
    200,
    1000
);

-- ============================================================
-- Templates globais (3 categorias: eletrônicos, casa, beleza)
-- ============================================================

-- Template: Eletrônicos
INSERT INTO copy_templates (
    id, tenant_id, category, name, version,
    title_template, description_template,
    variables, is_global, is_active
) VALUES (
    'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a01',
    NULL,
    'eletronicos',
    'Eletrônicos - Padrão v1',
    1,
    '{brand} {title} - {key_feature} | {condition}',
    E'## {title}\n\n**Marca:** {brand}\n**Modelo:** {model}\n**Condição:** {condition}\n\n### Características Principais\n{features}\n\n### Especificações Técnicas\n{specifications}\n\n### O que está incluso\n{included_items}\n\n---\n✅ Produto com garantia\n📦 Envio rápido\n🔒 Compra segura',
    '["brand", "title", "key_feature", "condition", "model", "features", "specifications", "included_items"]',
    true,
    true
);

-- Template: Casa e Decoração
INSERT INTO copy_templates (
    id, tenant_id, category, name, version,
    title_template, description_template,
    variables, is_global, is_active
) VALUES (
    'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a02',
    NULL,
    'casa',
    'Casa e Decoração - Padrão v1',
    1,
    '{brand} {title} - {material} {dimensions} | {style}',
    E'## {title}\n\n**Marca:** {brand}\n**Material:** {material}\n**Dimensões:** {dimensions}\n**Estilo:** {style}\n\n### Descrição\n{description}\n\n### Características\n{features}\n\n### Cuidados\n{care_instructions}\n\n---\n🏠 Transforme seu ambiente\n📦 Embalagem segura\n🚚 Envio para todo o Brasil',
    '["brand", "title", "material", "dimensions", "style", "description", "features", "care_instructions"]',
    true,
    true
);

-- Template: Beleza e Cuidados Pessoais
INSERT INTO copy_templates (
    id, tenant_id, category, name, version,
    title_template, description_template,
    variables, is_global, is_active
) VALUES (
    'b1eebc99-9c0b-4ef8-bb6d-6bb9bd380a03',
    NULL,
    'beleza',
    'Beleza e Cuidados - Padrão v1',
    1,
    '{brand} {title} {volume} - {benefit}',
    E'## {title}\n\n**Marca:** {brand}\n**Volume/Quantidade:** {volume}\n**Tipo de Pele/Cabelo:** {skin_type}\n\n### Benefícios\n{benefits}\n\n### Modo de Uso\n{usage_instructions}\n\n### Ingredientes Principais\n{key_ingredients}\n\n### Informações Importantes\n{warnings}\n\n---\n💄 Produto original\n📋 Registro ANVISA: {anvisa_registry}\n📦 Embalagem lacrada',
    '["brand", "title", "volume", "benefit", "skin_type", "benefits", "usage_instructions", "key_ingredients", "warnings", "anvisa_registry"]',
    true,
    true
);
