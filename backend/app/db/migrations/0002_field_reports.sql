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

create index if not exists idx_field_reports_zone_submitted on field_reports(zone_id, submitted_at desc);
