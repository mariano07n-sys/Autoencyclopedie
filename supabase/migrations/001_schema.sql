-- AutoEncyclopédie — schéma Supabase (PostgreSQL)
-- Exécuter dans : Supabase Dashboard → SQL Editor

CREATE TABLE IF NOT EXISTS brands (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    country TEXT,
    founded_year INTEGER,
    founder TEXT,
    headquarters TEXT,
    logo_url TEXT,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS models (
    id BIGSERIAL PRIMARY KEY,
    brand_id BIGINT NOT NULL REFERENCES brands(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    generation TEXT DEFAULT 'I',
    year_start INTEGER,
    year_end INTEGER,
    body_styles JSONB DEFAULT '[]'::jsonb,
    segment TEXT,
    description TEXT,
    anecdotes TEXT,
    image_urls JSONB DEFAULT '[]'::jsonb,
    thumbnail_url TEXT,
    countries JSONB DEFAULT '[]'::jsonb,
    is_iconic BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (brand_id, name, generation)
);

CREATE TABLE IF NOT EXISTS specs (
    id BIGSERIAL PRIMARY KEY,
    model_id BIGINT NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    variant_name TEXT,
    engine_type TEXT,
    engine_displacement REAL,
    fuel_type TEXT,
    power_hp INTEGER,
    power_kw INTEGER,
    torque_nm INTEGER,
    transmission TEXT,
    drive_type TEXT,
    cylinders INTEGER,
    acceleration_0_100 REAL,
    top_speed INTEGER,
    fuel_consumption REAL,
    co2_emissions INTEGER,
    weight_kg INTEGER,
    length_mm INTEGER,
    width_mm INTEGER,
    height_mm INTEGER,
    wheelbase_mm INTEGER,
    trunk_volume INTEGER,
    range_km INTEGER,
    price_launch_eur REAL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS agent_tasks (
    id BIGSERIAL PRIMARY KEY,
    task_type TEXT NOT NULL,
    target TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    items_processed INTEGER DEFAULT 0,
    items_added INTEGER DEFAULT 0,
    items_updated INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_cache (
    id BIGSERIAL PRIMARY KEY,
    query_hash TEXT UNIQUE NOT NULL,
    query TEXT NOT NULL,
    result TEXT,
    source TEXT DEFAULT 'gemini',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_models_brand ON models(brand_id);
CREATE INDEX IF NOT EXISTS idx_models_year ON models(year_start);
CREATE INDEX IF NOT EXISTS idx_specs_model ON specs(model_id);
CREATE INDEX IF NOT EXISTS idx_brands_name ON brands(name);
CREATE INDEX IF NOT EXISTS idx_models_name ON models(name);

-- Lecture publique pour le site (anon)
ALTER TABLE brands ENABLE ROW LEVEL SECURITY;
ALTER TABLE models ENABLE ROW LEVEL SECURITY;
ALTER TABLE specs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Public read brands" ON brands;
CREATE POLICY "Public read brands" ON brands FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Public read models" ON models;
CREATE POLICY "Public read models" ON models FOR SELECT TO anon, authenticated USING (true);

DROP POLICY IF EXISTS "Public read specs" ON specs;
CREATE POLICY "Public read specs" ON specs FOR SELECT TO anon, authenticated USING (true);
