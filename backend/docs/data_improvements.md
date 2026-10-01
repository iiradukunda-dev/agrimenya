Data & Modeling Improvements

Recommended additional datasets and steps to improve model performance:

- Historical SAS / AHS time series (multiple years):
  - Use past SAS and AHS rounds to build temporal features (year, trend),
    enable cross-year validation, and improve robustness to seasonality.

- Weather time series (daily or dekadal) per district:
  - Source: CHIRPS, ERA5, or Rwanda Met Service.
  - Derive rainfall accumulations, growing-season totals, and dry-spell
    features to explain year-to-year yield variation.

- Soil maps and permeability / fertility layers:
  - Source: ISRIC, AfSIS, or national soil surveys.
  - Use as static district-level covariates to improve baseline predictions.

- Remote sensing: NDVI/EVI time-series from Sentinel-2 / MODIS:
  - Capture in-season biomass trajectories to improve short-lead forecasts.

- Farm management / input access from AHS:
  - Fertilizer, improved seed, extension access, irrigation — these
    influence yield and intervention priority and are already partially
    incorporated via AHS constants.

Modeling improvements:

- Per-crop models or grouped models (cereals vs legumes) to reduce
  heterogeneity.
- Use quantile regression or conformal prediction for calibrated
  uncertainty estimates instead of constant confidence bands.
- Consider LightGBM/XGBoost hyperparameter tuning and feature
  interactions (soil x input use).
- Add cross-validation by district and by year for robust assessment.

CI / Ops suggestions:

- Store trained artifacts in a model registry (S3 or Git LFS) with
  model metadata (version, training date, dataset checksum).
- Add a small health endpoint `/health` that verifies model and DB
  connections and returns artifact versions.
