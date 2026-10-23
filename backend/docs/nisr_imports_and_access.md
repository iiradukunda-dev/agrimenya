# NISR data imports and access model

## NISR release import

The administrator page accepts one normalized CSV per district/crop/season release. Apply `app/db/migrations/0007_nisr_imports.sql` before enabling the import panel. The import endpoint is `POST /admin/nisr/imports`; the list endpoint is `GET /admin/nisr/imports`. Both require an authenticated named administrator session.

The CSV header is:

```csv
district,crop,season,yield_kg_ha,production_mt,cultivated_area_ha,harvested_area_ha
```

`district`, `crop`, `season`, and positive `yield_kg_ha` are required. Production, cultivated area, and harvested area may be blank. When production and harvested area are both present, the serving baseline is production divided by harvested area; older releases fall back to cultivated area, then the published yield value. Each file must contain one season label, such as `2026 Season C`. The source release title and original filename are stored with a SHA-256 digest. Repeated active files are rejected; failed imports can be retried. Rows are staged before activation, and incomplete writes are cleaned up where possible.

The yield-serving baseline now reads the latest active database releases, supplemented by existing `agri_metrics` rows where a release has no matching district/crop/season observation. It selects the requested season and year when available, otherwise the matching season across stored years. If there is no matching evidence, it returns no estimate. CSV training and evaluation files remain in offline retraining tools; the runtime image no longer needs the baseline CSV or baseline JSON.

When no validated yield model is deployed, priority is a same-crop district rank from those yield records: below the 25th percentile is High, the 25th to below the 50th is Medium, and the 50th percentile or above is Low. Ties use the midpoint rank. Fewer than 10 district observations are marked low evidence. The percentile is a transparent screening rule, not a calibrated risk probability or farm-level prediction.

The import accepts reviewed district-level release tables only; it is not a raw microdata ingestion endpoint. Apply migration `0012_nisr_harvested_area.sql` before using the `harvested_area_ha` column. When production and harvested area are present, yield aggregation uses harvested area; older releases fall back to cultivated area and then their published yield value. Household or plot-level files must stay in a restricted offline analysis workflow and must never be uploaded here.

For the SAS 2025 files, `python scripts/review_sas2025_microdata.py --input "path/to/Microdata.zip"` writes a disclosure-suppressed weighted-mean QA table under the ignored `backend/data/nisr_microdata_review/` directory. The output has a deliberately different schema from the admin importer, suppresses cells with effective sample size below 30, and is diagnostic only; it is not a design-based estimate or confidence interval and must not be treated as a production release. AHS 2024 individual/household microdata is not processed by this utility or injected into district-level plans.

The current serving-model training target is district/crop/season yield from the multi-year, report-derived `data/training_table.csv`. SAS 2025 plot records do not directly match the district-level prediction interface and contain only one agricultural year; fitting on those plots would create a different model whose inputs the app cannot currently supply. The supplied SAS microdata was therefore checked against its 2025 report-derived labels: 337 comparable cells, 0.5374% mean absolute percentage difference, and 92.28% within 1%; the largest difference was 18.3861% and needs source-method review. Summary and source hashes are in `data/eval/sas2025_microdata_validation.json`. The latest grouped model comparison (`data/eval/yield_model_evaluation.json`) selected `KEEP BASELINE`: no candidate beat the database/report baseline by the required margin on both held-out-district and held-out-season evaluations. No trained model artifact was activated.

For each newly released NISR dataset, the data steward still needs to map the published table into this normalized CSV format and identify its release title and season. The application validates the mapped rows but cannot determine whether an arbitrary source file has been interpreted correctly; review the source report and uploaded values before import.

## Access model

| Role | Intended access |
| --- | --- |
| Farmer / citizen | Their district/crops, practical advisories, their own plans and alerts, language and consent settings |
| Planner | Multi-zone comparisons, seasonal planning, draft alerts and implementation monitoring |
| Cooperative leader | Cooperative-scoped crop/member summaries, shared plans, and consent-based group alerts |
| NISR data steward | Validate and import official NISR releases; inspect import history |
| System administrator | Manage system configuration, accounts, zones, templates, and access audit |

Common public data guides, general crop/weather information, and basic alert access can be shared across user types. WhatsApp is an access channel for the same scoped services: a contact's phone identity and opt-in are required, and the bot must not grant administrative functions. Dataset upload remains a web administration task. Today the WhatsApp contact role is recorded, but all roles receive the same command menu; role-specific planner and cooperative workflows are not implemented yet.

Administrator actions use named accounts and time-limited bearer sessions. User write APIs still use a shared user API credential; individual farmer, planner, cooperative, or NISR-steward accounts and ownership/membership scopes are not implemented yet. Individual accounts for these roles, cooperative membership, zone ownership, and server-enforced per-role data scopes are required before treating the four user experiences as production-ready.
