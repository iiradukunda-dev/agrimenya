"""Estimate priority stability across leave-one-season-out training folds.

Run from backend: ``python -m scripts.evaluate_priority_stability``.
Each evaluated priority is produced from an OOF prediction while its entire
year/season group is excluded from model fitting. Crop benchmarks and area
reference percentiles are calculated from that fold's training rows.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import platform
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml.priority import apply_stability, classify_components

BACKEND = Path(__file__).resolve().parents[1]
TRAINING_PATH = BACKEND / "data" / "training_table.csv"
OOF_PATH = BACKEND / "data" / "eval" / "oof_predictions.csv"
MODEL_PATH = BACKEND / "app" / "ml" / "artifacts" / "yield_model.pkl"
OUTPUT_PATH = BACKEND / "data" / "eval" / "priority_stability.json"


def evaluate(training_path: Path = TRAINING_PATH, oof_path: Path = OOF_PATH,
             model_path: Path = MODEL_PATH, output_path: Path = OUTPUT_PATH) -> dict:
    training = pd.read_csv(training_path)
    oof = pd.read_csv(oof_path)
    if not {"district", "crop", "season_code", "year", "yield_kg_ha", "cultivated_area_ha"}.issubset(training.columns):
        raise ValueError("Training table lacks the sourced columns needed for stability evaluation")
    model_kind = None
    if model_path.is_file():
        import pickle
        with model_path.open("rb") as stream:
            bundle = pickle.load(stream)
        if bundle.get("feature_schema_version") == 2:
            model_kind = bundle.get("model_kind")
    prediction_column = model_kind if model_kind in oof.columns else "district_crop_season_weighted"
    test = oof[oof.split == "leave_one_season_out"].copy()
    area_lookup = training.set_index(["district", "crop", "season_code", "year"])["cultivated_area_ha"].to_dict()
    counts = training.groupby("crop").district.nunique().to_dict()
    values: dict[str, list[str]] = {}
    fold_count = int(test.fold.nunique())

    for fold, rows in test.groupby("fold", sort=True):
        try:
            year_text, season_text = str(fold).split(" Season ")
            year, code = int(year_text), season_text.strip()
        except ValueError:
            continue
        train = training[~((training.year.astype(int) == year) & (training.season_code.astype(str) == code))]
        for crop, crop_rows in rows.groupby("crop", sort=False):
            train_crop = train[(train.crop == crop) & (train.season_code.astype(str) == code) &
                               pd.to_numeric(train.yield_kg_ha, errors="coerce").gt(0)]
            train_crop = train_crop.sort_values("year", kind="stable").drop_duplicates("district", keep="last")
            if train_crop.empty:
                continue
            benchmark = float(pd.to_numeric(train_crop.yield_kg_ha, errors="coerce").quantile(0.75))
            crop_mean = float(pd.to_numeric(train_crop.yield_kg_ha, errors="coerce").mean())
            exposure = pd.to_numeric(train_crop.cultivated_area_ha, errors="coerce").dropna()
            if model_kind and model_kind in oof.columns:
                lodo = oof[(oof.split == "leave_one_district_out") & (oof.crop == crop)]
                residual = (pd.to_numeric(lodo.actual_yield_kg_ha, errors="coerce") -
                            pd.to_numeric(lodo[model_kind], errors="coerce")).dropna()
                residual_se = float(residual.std(ddof=1)) if len(residual) > 1 else None
            else:
                residual_se = None
            for row in crop_rows.itertuples(index=False):
                key = (str(row.district), str(row.crop), str(row.season_code), int(row.year))
                raw_area = area_lookup.get(key)
                area = float(raw_area) if raw_area is not None and pd.notna(raw_area) else None
                area_pct = float((exposure <= area).mean()) if area is not None and len(exposure) else None
                actual = float(row.actual_yield_kg_ha)
                prediction = float(getattr(row, prediction_column)) if pd.notna(getattr(row, prediction_column)) else actual
                yield_index = actual / crop_mean if crop_mean > 0 else None
                result = classify_components(
                    observed_yield=actual, expected_yield=prediction if model_kind else None,
                    residual_se=residual_se, top_quartile_yield=benchmark,
                    cultivated_area_ha=area, area_percentile=area_pct,
                    yield_index=yield_index, crop_district_count=int(counts.get(crop, 0)),
                    model_available=bool(model_kind),
                )
                identity = f"{row.district}|{row.crop}"
                values.setdefault(identity, []).append(result["underlying_priority_level"])

    by_identity = {}
    changes = 0
    uncertain = 0
    for identity, labels in values.items():
        result = apply_stability({"priority_level": labels[-1], "underlying_priority_level": labels[-1],
                                  "priority_status": "evaluated", "low_evidence": False, "reasons": []}, labels)
        changes += result["priority_changes_across_folds"]
        uncertain += result["priority_status"] == "uncertain"
        by_identity[identity] = {"fold_priorities": labels, "priority_changes_across_folds": result["priority_changes_across_folds"],
                                 "priority_level": result["priority_level"], "underlying_priority_level": labels[-1],
                                 "uncertain": result["priority_status"] == "uncertain"}
    sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    report = {"schema_version": 1, "split": "leave_one_season_out",
              "folds_run": fold_count, "prediction_column": prediction_column,
              "model_available": bool(model_kind), "district_crop_combinations": len(by_identity),
              "uncertain_combinations": int(uncertain), "priority_changes_across_folds": int(changes),
              "training_date_utc": datetime.now(timezone.utc).isoformat(),
              "random_seed": 42, "randomness_used": False,
              "versions": {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__},
              "input_hashes": {"training_table_sha256": sha(training_path), "oof_predictions_sha256": sha(oof_path)},
              "by_district_crop": by_identity}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Leave-one-season-out stability: {fold_count} folds; {len(by_identity)} district/crop combinations; "
          f"{uncertain} uncertain; {changes} priority changes. Saved {output_path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training", type=Path, default=TRAINING_PATH)
    parser.add_argument("--oof", type=Path, default=OOF_PATH)
    parser.add_argument("--model", type=Path, default=MODEL_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    evaluate(args.training, args.oof, args.model, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
