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
    priority_level  text check (priority_level in ('Low', 'Medium', 'High', 'Unknown')),
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
    crop            text,
    action          text,
    status          text not null default 'draft' check (status in ('draft', 'approved')),
    approved_by     text,
    approved_at     timestamptz,
    allow_links     boolean not null default false,
    created_by      text,
    created_at      timestamptz default now()
);

-- WhatsApp contact and delivery data is server-only: RLS is enabled without
-- public policies so only the backend service role can access these tables.
create table if not exists contacts (
    id uuid primary key default gen_random_uuid(),
    display_name text,
    role text check (role in ('planner', 'extension_officer', 'cooperative_leader', 'farmer', 'other')),
    phone_e164 text,
    bsuid text,
    language text not null default 'en' check (language in ('en', 'rw')),
    zone_id uuid references zones(id),
    crops text[] not null default '{}',
    whatsapp_opt_in boolean not null default false,
    opt_in_at timestamptz,
    opt_in_source text,
    opt_in_text_version text,
    opt_out_at timestamptz,
    last_inbound_at timestamptz,
    undeliverable_count integer not null default 0 check (undeliverable_count >= 0),
    bot_unknown_count smallint not null default 0 check (bot_unknown_count >= 0),
    last_rate_limit_notice_at timestamptz,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    deleted_at timestamptz,
    constraint contacts_identity_required check (phone_e164 is not null or bsuid is not null or deleted_at is not null),
    constraint contacts_phone_e164_check check (phone_e164 is null or phone_e164 ~ '^\+[1-9][0-9]{7,14}$')
);
create unique index if not exists contacts_phone_e164_unique
    on contacts(phone_e164) where phone_e164 is not null;
create unique index if not exists contacts_bsuid_unique
    on contacts(bsuid) where bsuid is not null;
create index if not exists contacts_last_inbound_at_idx on contacts(last_inbound_at);

create table if not exists whatsapp_templates (
    name text not null,
    language text not null,
    category text not null check (category in ('utility', 'authentication', 'marketing')),
    status text not null default 'draft' check (status in ('draft', 'submitted', 'approved', 'rejected', 'paused')),
    body_preview text,
    param_count integer not null default 0 check (param_count >= 0),
    primary key (name, language)
);

create table if not exists message_log (
    id uuid primary key default gen_random_uuid(),
    direction text not null check (direction in ('outbound', 'inbound')),
    contact_id uuid references contacts(id),
    wa_message_id text unique,
    kind text not null check (kind in ('alert', 'plan_share', 'bot_reply', 'optin_confirm', 'optout_confirm', 'digest')),
    template_name text,
    status text not null check (status in ('queued', 'sent', 'delivered', 'read', 'failed', 'received')),
    error_code text,
    error_detail text,
    alert_id uuid references alerts(id),
    plan_id uuid references plans(id),
    body_hash text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);
create index if not exists message_log_contact_created_idx on message_log(contact_id, created_at desc);
create unique index if not exists message_log_alert_contact_unique
    on message_log(alert_id, contact_id) where alert_id is not null and contact_id is not null and direction = 'outbound';

create table if not exists webhook_events (
    event_key text primary key,
    received_at timestamptz not null default now(),
    payload_type text not null
);

create table if not exists alert_subscriptions (
    id uuid primary key default gen_random_uuid(),
    contact_id uuid not null references contacts(id) on delete cascade,
    zone_id uuid references zones(id) on delete cascade,
    crop text,
    min_severity text not null default 'warning' check (min_severity in ('info', 'warning', 'critical')),
    unique (contact_id, zone_id, crop)
);
create unique index if not exists alert_subscriptions_scope_unique
    on alert_subscriptions(contact_id, coalesce(zone_id, '00000000-0000-0000-0000-000000000000'::uuid), coalesce(crop, ''));

comment on table contacts is 'WhatsApp identity and consent records. RLS has no public policies; access is server-side only.';
comment on table whatsapp_templates is 'Approved WhatsApp template registry. RLS has no public policies; access is server-side only.';
comment on table message_log is 'Message delivery metadata and body hashes only; message bodies and credentials are never stored here.';
comment on table webhook_events is 'Webhook idempotency keys only. RLS has no public policies; access is server-side only.';
comment on table alert_subscriptions is 'Contact alert preferences. RLS has no public policies; access is server-side only.';

alter table contacts enable row level security;
alter table whatsapp_templates enable row level security;
alter table message_log enable row level security;
alter table webhook_events enable row level security;
alter table alert_subscriptions enable row level security;

create table if not exists field_reports (
    id                  uuid primary key default gen_random_uuid(),
    zone_id             uuid not null references zones(id) on delete cascade,
    district            text not null,
    crop                text not null,
    rainfall_mm         double precision check (rainfall_mm is null or rainfall_mm between 0 and 1000),
    soil_moisture_pct   double precision check (soil_moisture_pct is null or soil_moisture_pct between 0 and 100),
    symptoms            text not null default '',
    notes               text not null default '',
    submitted_at        timestamptz not null default now()
);

create table if not exists zone_readiness (
    zone_id             uuid primary key references zones(id) on delete cascade,
    finance_evidence   jsonb not null default '{}'::jsonb,
    export_evidence    jsonb not null default '{}'::jsonb,
    updated_at          timestamptz not null default now()
);

create table if not exists zone_work_records (
    id                  uuid primary key default gen_random_uuid(),
    zone_id             uuid not null references zones(id) on delete cascade,
    season              text not null,
    crop                text not null,
    worker_days         double precision not null check (worker_days >= 0),
    notes               text not null default '',
    recorded_at         timestamptz not null default now()
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
create index if not exists idx_field_reports_zone_submitted on field_reports(zone_id, submitted_at desc);
create index if not exists idx_zone_work_records_zone_recorded on zone_work_records(zone_id, recorded_at desc);
