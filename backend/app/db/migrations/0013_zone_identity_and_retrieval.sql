-- Stable zone identity, safe duplicate marking, and indexes for paged lookups.
-- This migration marks legacy duplicates; it deliberately does not delete or merge rows.

alter table zones add column if not exists identity_key text;
alter table zones add column if not exists duplicate_of uuid references zones(id) on delete set null;

with normalized as (
    select
        id,
        lower(btrim(regexp_replace(coalesce(district, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(sector, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(cell, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(crop_type, ''), '[[:space:]]+', ' ', 'g'))) || '|' ||
        lower(btrim(regexp_replace(coalesce(season, ''), '[[:space:]]+', ' ', 'g'))) as identity_key,
        first_value(id) over (
            partition by
                lower(btrim(regexp_replace(coalesce(district, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(sector, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(cell, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(crop_type, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(season, ''), '[[:space:]]+', ' ', 'g')))
            order by created_at nulls last, id
        ) as canonical_id,
        row_number() over (
            partition by
                lower(btrim(regexp_replace(coalesce(district, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(sector, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(cell, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(crop_type, ''), '[[:space:]]+', ' ', 'g'))),
                lower(btrim(regexp_replace(coalesce(season, ''), '[[:space:]]+', ' ', 'g')))
            order by created_at nulls last, id
        ) as identity_rank
    from zones
), marked as (
    select id,
           case when identity_rank = 1 then identity_key else null end as identity_key,
           case when identity_rank = 1 then null else canonical_id end as duplicate_of
    from normalized
)
update zones as target
set identity_key = marked.identity_key,
    duplicate_of = marked.duplicate_of
from marked
where target.id = marked.id;

create unique index if not exists zones_identity_key_unique
    on zones(identity_key) where identity_key is not null;
create index if not exists zones_district_created_idx
    on zones(lower(district), created_at desc, id);
create index if not exists agri_metrics_crop_season_zone_idx
    on agri_metrics(crop, season, zone_id);
