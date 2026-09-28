"""
Trains the yield model on real NISR SAS 2026 Season A/B data
(district x crop x season -> yield_kg_ha, 1,253 real observations).

Run once (and again whenever new SAS data lands):
    python -m app.ml.train_yield_model

Produces two artifacts in app/ml/artifacts/:
  - yield_model.pkl        XGBoost regressor + label encoders (primary model)
  - yield_baselines.json   crop / district-crop average yields (fallback lookup
                            for combinations too sparse for the model, and for
                            sanity-checking predictions in the demo)

Both are consumed by app/ml/predict.py.
"""
import json
import pickle
from pathlib import Path

import logging
import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score

# Prefer XGBoost when available (better performance). If the import fails
# (e.g. wheel/C library mismatch on the host), fall back to a RandomForest
# so the training script remains runnable in constrained environments.
try:
    from xgboost import XGBRegressor
    _USE_XGB = True
except Exception:
    logging.exception("XGBoost import failed; falling back to RandomForestRegressor")
    from sklearn.ensemble import RandomForestRegressor
    XGBRegressor = None  # keep name absent
    _USE_XGB = False

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

# Real SAS 2026 Season A + Season B data (30 districts x 23 crops x 2 seasons).
DEFAULT_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "agri_menya_real_data.csv"


def build_baselines(df: pd.DataFrame) -> dict:
    overall_avg = round(df["yield_kg_ha"].mean(), 1)
    crop_avg = df.groupby("crop")["yield_kg_ha"].mean().round(1).to_dict()
    district_crop_avg = (
        df.groupby(["district", "crop"])["yield_kg_ha"].mean().round(1)
    )
    district_crop_avg = {f"{d}|{c}": v for (d, c), v in district_crop_avg.items()}
    return {
        "overall_average": overall_avg,
        "crop_averages": crop_avg,
        "district_crop_averages": district_crop_avg,
    }


def train(data_path: Path = DEFAULT_DATA_PATH) -> None:
    df = pd.read_csv(data_path)
    df = df.dropna(subset=["yield_kg_ha", "cultivated_area_ha", "district", "crop", "season"])

    district_enc = LabelEncoder().fit(df["district"])
    crop_enc = LabelEncoder().fit(df["crop"])
    season_enc = LabelEncoder().fit(df["season"])

    X = pd.DataFrame({
        "district": district_enc.transform(df["district"]),
        "crop": crop_enc.transform(df["crop"]),
        "season": season_enc.transform(df["season"]),
        "cultivated_area_ha": df["cultivated_area_ha"].values,
    })
    y = df["yield_kg_ha"].values

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    if _USE_XGB:
        model = XGBRegressor(
            n_estimators=200, max_depth=4, learning_rate=0.08,
            subsample=0.9, colsample_bytree=0.9, random_state=42,
        )
    else:
        from sklearn.ensemble import RandomForestRegressor
        model = RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)

    model.fit(X_train, y_train)

    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2 = r2_score(y_test, preds)
    print(f"Trained on {len(df)} real SAS rows | test MAE={mae:.1f} kg/ha, R2={r2:.3f}")

    bundle = {
        "model": model,
        "district_encoder": district_enc,
        "crop_encoder": crop_enc,
        "season_encoder": season_enc,
        "feature_order": ["district", "crop", "season", "cultivated_area_ha"],
        "model_version": "xgboost-v1-sas2026" if _USE_XGB else "rf-v1-sas2026",
    }
    with open(ARTIFACTS_DIR / "yield_model.pkl", "wb") as f:
        pickle.dump(bundle, f)

    baselines = build_baselines(df)
    with open(ARTIFACTS_DIR / "yield_baselines.json", "w") as f:
        json.dump(baselines, f, indent=2)

    print(f"Saved model -> {ARTIFACTS_DIR / 'yield_model.pkl'}")
    print(f"Saved baselines -> {ARTIFACTS_DIR / 'yield_baselines.json'}")


if __name__ == "__main__":
    train()
