-- Versioned NISR yield data imports. New datasets are staged and only become
-- visible to prediction after every row has been written successfully.
create table if not exists nisr_imports (
    id uuid primary key default gen_random_uuid(),
    source_filename text not null,
    source_release text not null,
    season text not null,
    sha256 text not null unique,
    status text not null default 'staging'
        check (status in ('staging', 'active', 'failed')),
    row_count integer not null default 0 check (row_count >= 0),
    imported_by text not null,
    error_detail text,
    created_at timestamptz not null default now(),
    activated_at timestamptz
);

create index if not exists nisr_imports_active_season_idx
    on nisr_imports(season, activated_at desc) where status = 'active';

create table if not exists nisr_yield_records (
    id uuid primary key default gen_random_uuid(),
    import_id uuid not null references nisr_imports(id) on delete cascade,
    district text not null,
    crop text not null,
    season text not null,
    yield_kg_ha double precision not null check (yield_kg_ha > 0),
    production_mt double precision check (production_mt is null or production_mt >= 0),
    cultivated_area_ha double precision check (cultivated_area_ha is null or cultivated_area_ha > 0),
    created_at timestamptz not null default now(),
    unique (import_id, district, crop, season)
);

create index if not exists nisr_yield_records_lookup_idx
    on nisr_yield_records(district, crop, season);

alter table nisr_imports enable row level security;
alter table nisr_yield_records enable row level security;

comment on table nisr_imports is 'Audited NISR release imports. Service-role access only.';
comment on table nisr_yield_records is 'Validated NISR yield observations linked to their source import. Service-role access only.';
