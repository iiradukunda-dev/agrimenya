# Zone and yield data provenance

Audit performed 23 October 2026 against the running development API and the files in this repository.

## Yield observations

- The API returned 1,246 `agri_metrics` rows. Each row matched `backend/data/agri_menya_real_data.csv` on district, crop, season, yield, production, and cultivated area: 1,246 of 1,246 exact matches.
- The local source CSV has 1,253 rows. Its seven blank-yield rows are intentionally skipped by `backend/scripts/seed_real_data.py`.
- The seed script describes this file as an extraction of Rwanda Seasonal Agricultural Survey (SAS) 2026 Season A/B data. This verifies the live values against the project’s declared seed source; it does not independently re-audit the original NISR report extraction.
- Predictions use an observational district/crop baseline from database evidence, supplemented by bundled official NISR SAS history when no matching database row exists. `/health/status` reports `model_present: false`; there is no trained ML model serving predictions.
- The current `predictions` table retains crop, season, model version, priority, and output, but not evidence source, period, or scope. For older saved predictions, the exact evidence mix cannot be reconstructed from the saved prediction row alone. The zone UI labels this limitation. A new prediction response reports source details when available.

## Zone registry and maps

- The API returned 36 zone records. Twenty-nine have no sector or cell and use coordinates matching the approximate district reference centroids in `backend/app/db/rwanda_districts.py`; these are district-level records, not surveyed farm locations. The map now omits them as point markers.
- The remaining seven records have submitted coordinates. The application has not independently verified those coordinates or the entered sector/cell values.
- Zone crop and season fields are registry inputs. One live zone is registered as `maizes` while its latest saved prediction is for Banana in Season A 2026. The client now suppresses saved output and priority unless the saved assessment matches the zone’s registered crop and, when set, season. Recommendations for a different crop or season are not presented as current zone guidance.
- District polygons are the NISR 2022 administrative boundary snapshot documented in `frontend/data/README.md`. Shading summarizes filtered records; it is not a farm boundary or a claim about every farm in a district.

## Other zone indicators

- Finance readiness is a user-reported checklist. The current form does not upload or verify supporting documents; completion is not a credit score or approval.
- Nutrition risk, climate risk, credit scoring, and export readiness do not have validated calculation methods configured. Missing values must remain “Not assessed.”
- Field reports and worker-day entries are user-submitted observations, not official NISR records.

## Duplicate handling and retrieval

- Zone identity is normalized from district, sector, cell, crop, and season. New registrations return the existing record when that identity is already present.
- Migration `0013_zone_identity_and_retrieval.sql` backfills the identity key and marks repeated identities with `duplicate_of`; it preserves every row and does not merge or delete linked records. Apply it in the Supabase SQL editor before relying on the database unique index. The application has a compatibility lookup while the migration is pending.
- The Zones screen uses `/segmentation/zones/page` for server-side filters and bounded pages (25, 50, or 100 records); `/segmentation/zones/summary` supplies registry totals. `/segmentation/agri-metrics/page` provides the same paging pattern for yield observations.
- A previous live audit found six Rubavu rows with three repeated district/sector/cell/crop/season identities. The records remain untouched pending review of dependent predictions and observations. This audit could not verify dependent links in the current restricted session.
