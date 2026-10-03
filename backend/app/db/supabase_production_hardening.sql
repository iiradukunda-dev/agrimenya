-- Production hardening migration for Agri-Menya Supabase
-- Run this in the Supabase SQL editor or via migration tooling.
-- This adds the missing operational controls that are useful in production:
-- 1) Admin audit trail
-- 2) Updated timestamps
-- 3) Performance indexes
-- 4) Optional RLS starter policies

begin;

-- -----------------------------------------------------------------------------
-- 1) Audit trail for privileged actions
-- -----------------------------------------------------------------------------
create table if not exists admin_audit_log (
    id uuid primary key default gen_random_uuid(),
    actor_id text,
    actor_role text,
    action text not null,
    table_name text,
    record_id text,
    metadata jsonb default '{}'::jsonb,
    ip_address text,
    user_agent text,
    created_at timestamptz not null default now()
);

create index if not exists idx_admin_audit_log_created_at
    on admin_audit_log (created_at desc);

create index if not exists idx_admin_audit_log_actor
    on admin_audit_log (actor_id, actor_role, created_at desc);

-- -----------------------------------------------------------------------------
-- 2) Updated timestamps for common tables
-- -----------------------------------------------------------------------------
alter table if exists zones add column if not exists updated_at timestamptz default now();
alter table if exists agri_metrics add column if not exists updated_at timestamptz default now();
alter table if exists predictions add column if not exists updated_at timestamptz default now();
alter table if exists plans add column if not exists updated_at timestamptz default now();
alter table if exists alerts add column if not exists updated_at timestamptz default now();

create or replace function set_updated_at()
returns trigger as $$
begin
    new.updated_at = now();
    return new;
end;
$$ language plpgsql;

-- Zones
drop trigger if exists trg_zones_updated_at on zones;
create trigger trg_zones_updated_at
before update on zones
for each row execute procedure set_updated_at();

-- Agri metrics
drop trigger if exists trg_agri_metrics_updated_at on agri_metrics;
create trigger trg_agri_metrics_updated_at
before update on agri_metrics
for each row execute procedure set_updated_at();

-- Predictions
drop trigger if exists trg_predictions_updated_at on predictions;
create trigger trg_predictions_updated_at
before update on predictions
for each row execute procedure set_updated_at();

-- Plans
drop trigger if exists trg_plans_updated_at on plans;
create trigger trg_plans_updated_at
before update on plans
for each row execute procedure set_updated_at();

-- Alerts
drop trigger if exists trg_alerts_updated_at on alerts;
create trigger trg_alerts_updated_at
before update on alerts
for each row execute procedure set_updated_at();

-- -----------------------------------------------------------------------------
-- 3) Indexes to improve filtering and reporting performance
-- -----------------------------------------------------------------------------
create index if not exists idx_zones_district
    on zones (district);

create index if not exists idx_zones_season
    on zones (season);

create index if not exists idx_agri_metrics_season_crop
    on agri_metrics (season, crop);

create index if not exists idx_agri_metrics_zone_season
    on agri_metrics (zone_id, season);

create index if not exists idx_predictions_zone_season
    on predictions (zone_id, season);

create index if not exists idx_predictions_created_at
    on predictions (created_at desc);

create index if not exists idx_alerts_zone_created_at
    on alerts (zone_id, created_at desc);

create index if not exists idx_plans_zone_created_at
    on plans (zone_id, created_at desc);

-- -----------------------------------------------------------------------------
-- 4) Optional starter RLS (enable only if you are using Supabase Auth)
--    Keep this commented or disable it until your auth model is fully defined.
-- -----------------------------------------------------------------------------
-- alter table if exists zones enable row level security;
-- alter table if exists agri_metrics enable row level security;
-- alter table if exists predictions enable row level security;
-- alter table if exists plans enable row level security;
-- alter table if exists alerts enable row level security;
--
-- create policy "zones_select_authenticated"
-- on zones for select
-- using (auth.role() = 'authenticated');
--
-- create policy "agri_metrics_select_authenticated"
-- on agri_metrics for select
-- using (auth.role() = 'authenticated');
--
-- create policy "predictions_select_authenticated"
-- on predictions for select
-- using (auth.role() = 'authenticated');

commit;
