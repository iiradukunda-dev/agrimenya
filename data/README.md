# Project data

The project datasets are stored in [`../backend/data/`](../backend/data/).
They support the app's district/crop evidence and offline data preparation and
evaluation workflows.

Key files include:

- `nisr_official_yields_2022_2026.csv` — normalized district, crop, season,
  yield, production, and area observations used for official yield evidence.
- `agri_menya_real_data.csv` — normalized district/crop/season agricultural
  data for the real-data seeding workflow.
- `training_table.csv` — prepared features and yield observations for offline
  analysis and model experiments.
- `external/` — external weather data used in offline experiments.
- `eval/` — evaluation outputs and quality checks.

The normalized NISR yield CSV is also bundled at
[`../frontend/data/nisr_official_yields_2022_2026.csv`](../frontend/data/nisr_official_yields_2022_2026.csv)
so district evidence and crop comparisons remain available if the live API is
temporarily unreachable. Keep that frontend copy synchronized with the
canonical backend dataset.

The runtime API reads active yield observations from Supabase; the offline
files are not a substitute for importing and validating production data. Check
the dataset source, access terms, and preparation notes before reusing data.
See [`../backend/docs/nisr_imports_and_access.md`](../backend/docs/nisr_imports_and_access.md),
[`../backend/docs/zone_data_provenance.md`](../backend/docs/zone_data_provenance.md),
and [`../backend/docs/retraining.md`](../backend/docs/retraining.md).
