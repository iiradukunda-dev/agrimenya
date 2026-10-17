# NISR data imports and access model

## NISR release import

The administrator page accepts one normalized CSV per district/crop/season release. Apply `app/db/migrations/0007_nisr_imports.sql` before enabling the import panel. The import endpoint is `POST /admin/nisr/imports`; the list endpoint is `GET /admin/nisr/imports`. Both require an authenticated named administrator session.

The CSV header is:

```csv
district,crop,season,yield_kg_ha,production_mt,cultivated_area_ha
```

`district`, `crop`, `season`, and positive `yield_kg_ha` are required. Production and cultivated area may be blank; when both are present, the baseline is production divided by area. Each file must contain one season label, such as `2026 Season C`. The source release title and original filename are stored with a SHA-256 digest. Repeated active files are rejected; failed imports can be retried. Rows are staged before activation, and incomplete writes are cleaned up where possible.

The yield-serving baseline now reads the latest active database releases, supplemented by existing `agri_metrics` rows where a release has no matching district/crop/season observation. It selects the requested season and year when available, otherwise the matching season across stored years. If there is no matching evidence, it returns no estimate. CSV training and evaluation files remain in offline retraining tools; the runtime image no longer needs the baseline CSV or baseline JSON.

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
