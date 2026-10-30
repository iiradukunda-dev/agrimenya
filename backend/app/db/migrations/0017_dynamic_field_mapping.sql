-- Keep mapped farm sites distinct and optionally store farmer-drawn field outlines.
alter table zones add column if not exists site_name text;
alter table zones add column if not exists field_boundary_geojson jsonb;
-- Older zone tables may predate creation timestamps; add one before using it
-- to select a stable canonical record when duplicate identities are repaired.
alter table zones add column if not exists created_at timestamptz not null default now();

do $$
begin
    if not exists (
        select 1 from pg_constraint
        where conname = 'zones_field_boundary_geojson_polygon'
          and conrelid = 'zones'::regclass
    ) then
        alter table zones
            add constraint zones_field_boundary_geojson_polygon
            check (
                field_boundary_geojson is null or (
                    jsonb_typeof(field_boundary_geojson) = 'object'
                    and field_boundary_geojson ->> 'type' = 'Polygon'
                    and jsonb_typeof(field_boundary_geojson -> 'coordinates') = 'array'
                )
            );
    end if;
end $$;

-- Include the chosen map location and optional site label in identity. Two farms
-- in the same cell/crop/season can now be registered at different coordinates.
drop index if exists zones_identity_key_unique;

with normalized as (
    select
        id,
        created_at,
        lower(btrim(regexp_replace(coalesce(district, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(sector, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(cell, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(crop_type, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(season, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(site_name, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        round(latitude::numeric, 6)::text || '|' || round(longitude::numeric, 6)::text as identity_key
    from zones
), ranked as (
    select id, identity_key,
        first_value(id) over (partition by identity_key order by created_at nulls last, id) as canonical_id,
        row_number() over (partition by identity_key order by created_at nulls last, id) as identity_rank
    from normalized
)
update zones as target
set identity_key = case when ranked.identity_rank = 1 then ranked.identity_key else null end,
    duplicate_of = case when ranked.identity_rank = 1 then null else ranked.canonical_id end
from ranked
where target.id = ranked.id;

create unique index zones_identity_key_unique
    on zones(identity_key) where identity_key is not null;

comment on column zones.site_name is
    'Optional user-provided farm or site label used to distinguish mapped locations.';
comment on column zones.field_boundary_geojson is
    'Optional farmer-drawn GeoJSON polygon; indicative field outline, not a legal parcel boundary.';
