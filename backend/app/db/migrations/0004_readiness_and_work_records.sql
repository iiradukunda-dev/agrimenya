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

create index if not exists idx_zone_work_records_zone_recorded
    on zone_work_records(zone_id, recorded_at desc);
