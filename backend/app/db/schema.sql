-- Agri-Menya database schema
-- Run this in the Supabase SQL editor (or via `supabase db push`)
--
-- If agri_metrics / predictions already exist from an earlier run
-- (before the `crop` field was added), run this migration block first
-- so `create table if not exists` below doesn't silently skip them:
--
--   alter table if exists agri_metrics add column if not exists crop text not null default 'All crops';
--   alter table if exists agri_metrics add column if not exists production_mt double precision;
--   alter table if exists predictions  add column if not exists crop text not null default 'All crops';
--   alter table if exists agri_metrics
--       add constraint if not exists agri_metrics_zone_season_crop_key unique (zone_id, season, crop);

create table if not exists zones (
    id              uuid primary key default gen_random_uuid(),
    district        text not null,
    sector          text,
    cell            text,
    latitude        double precision not null,
    longitude       double precision not null,
    crop_type       text,
    season          text,               -- e.g. 'Season A 2026', 'Season B 2025', 'Annual 2025'
    created_at      timestamptz default now()
);

create table if not exists agri_metrics (
    id              uuid primary key default gen_random_uuid(),
    zone_id         uuid references zones(id) on delete cascade,
    season          text not null,
    crop            text not null default 'All crops',  -- NISR SAS crop name, e.g. 'Maize', 'Cassava'
    yield_actual    double precision,      -- kg/ha (SAS yield_kg_ha)
    production_mt   double precision,      -- metric tons produced (SAS production_mt)
    rainfall_mm     double precision,
    soil_type       text,
    area_cultivated double precision,      -- hectares (SAS cultivated_area_ha)
    household_size  double precision,
    created_at      timestamptz default now(),
    unique (zone_id, season, crop)         -- makes seeding idempotent (upsert-safe)
);

create table if not exists predictions (
    id              uuid primary key default gen_random_uuid(),
    zone_id         uuid references zones(id) on delete cascade,
    season          text not null,
    crop            text not null default 'All crops',
    predicted_yield double precision,
    priority_level  text check (priority_level in ('Low', 'Medium', 'High')),
    confidence      double precision,      -- 0.0 - 1.0
    model_version   text,
    created_at      timestamptz default now()
);

-- Pillar 5: National Alignment (NST2 / Vision 2050)
create table if not exists alignment_metrics (
    id                      uuid primary key default gen_random_uuid(),
    zone_id                 uuid references zones(id) on delete cascade,
    season                  text not null,
    irrigation_ha           double precision default 0,
    terraces_ha             double precision default 0,
    credit_insurance_score  double precision,           -- 0-100
    nutrition_risk_level    text check (nutrition_risk_level in ('Low', 'Medium', 'High')),
    climate_risk_level      text check (climate_risk_level in ('Low', 'Medium', 'High')),
    female_managed_share    double precision,           -- 0.0 - 1.0, if available
    export_readiness_flag   boolean default false,
    estimated_jobs_supported integer default 0,
    created_at              timestamptz default now()
);

create table if not exists plans (
    id              uuid primary key default gen_random_uuid(),
    zone_id         uuid references zones(id) on delete cascade,
    title           text not null,
    roadmap_json    jsonb,
    resources_json  jsonb,
    created_by      text,
    created_at      timestamptz default now()
);

create table if not exists alerts (
    id              uuid primary key default gen_random_uuid(),
    zone_id         uuid references zones(id) on delete cascade,
    message         text not null,
    severity        text check (severity in ('Info', 'Warning', 'Critical')),
    created_by      text,
    created_at      timestamptz default now()
);

create table if not exists users (
    id              uuid primary key default gen_random_uuid(),
    name            text not null,
    role            text check (role in ('planner', 'extension_officer', 'cooperative_leader')),
    email           text unique,
    created_at      timestamptz default now()
);

-- Helpful indexes
create index if not exists idx_agri_metrics_zone on agri_metrics(zone_id);
create index if not exists idx_predictions_zone on predictions(zone_id);
create index if not exists idx_alignment_zone on alignment_metrics(zone_id);
create index if not exists idx_plans_zone on plans(zone_id);
create index if not exists idx_alerts_zone on alerts(zone_id);
