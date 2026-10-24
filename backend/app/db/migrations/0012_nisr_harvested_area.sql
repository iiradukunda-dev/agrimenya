-- Keep the official harvested-area denominator distinct from cultivated area.
alter table nisr_yield_records
    add column if not exists harvested_area_ha double precision
    check (harvested_area_ha is null or harvested_area_ha > 0);

comment on column nisr_yield_records.harvested_area_ha is
    'Official harvested crop area in hectares; distinct from cultivated area for yield calculations.';
