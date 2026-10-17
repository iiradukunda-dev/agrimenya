"""Evaluate NISR yield baselines with grouped district and season holdouts.

Run from backend:
    python -m scripts.evaluate_baselines

Writes data/eval/baselines.json and the out-of-fold predictions used to
calculate it to data/eval/baseline_predictions.csv.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import numpy as np

from app.ml.validation import METHODS, evaluate_predictions, grouped_oof_predictions, runtime_versions

BACKEND = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = BACKEND / "data" / "training_table.csv"
DEFAULT_OUTPUT = BACKEND / "data" / "eval" / "baselines.json"

METHOD_LABELS = {
    "crop_mean": "Crop mean",
    "crop_season_mean": "Crop x season-code mean",
    "district_crop_season_weighted": "District-crop-season weighted; crop fallback",
    "previous_season_same_district_crop": "Previous-season district-crop",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if pd.isna(value):
        return None
    return value


def _format(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    try:
        return f"{float(value):.{digits}f}"
    except (TypeError, ValueError):
        return "n/a"


def print_table(split_name: str, result: dict[str, Any], split_info: dict[str, Any]) -> None:
    print(f"\n{split_name.replace('_', ' ').title()} — {split_info['folds_run']}/{split_info['groups']} folds ({split_info['status']})")
    headers = ["Method", "N", "Coverage", "MAE kg/ha", "MAE % mean", "RMSE", "Within MAE", "Within MAE %", "Within RMSE", "Within R²", "Spearman", "Top-6 overlap"]
    rows = []
    for method in METHODS:
        metrics = result[method]
        rows.append([
            METHOD_LABELS[method], str(metrics.get("n", 0)), _format(metrics.get("coverage")),
            _format(metrics.get("mae_kg_ha"), 1), _format(metrics.get("mae_pct_crop_mean"), 1),
            _format(metrics.get("rmse_kg_ha"), 1),
            _format(metrics.get("within_crop", {}).get("macro_mae_kg_ha"), 1),
            _format(metrics.get("within_crop", {}).get("macro_mae_pct_crop_mean"), 1),
            _format(metrics.get("within_crop", {}).get("macro_rmse_kg_ha"), 1),
            _format(metrics.get("within_crop", {}).get("centered_r2")),
            _format(metrics.get("spearman_rank_correlation")), _format(metrics.get("top6_overlap_share")),
        ])
    widths = [max(len(headers[i]), *(len(row[i]) for row in rows)) for i in range(len(headers))]
    print(" | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("-+-".join("-" * width for width in widths))
    for row in rows:
        print(" | ".join(row[i].ljust(widths[i]) for i in range(len(row))))
    print("Within columns macro-average crop metrics; within-crop R² centers actual and predicted yields by each crop's held-out actual mean.")
    for method in METHODS:
        thin = result[method].get("thin_crop_summary", {})
        print(f"  {METHOD_LABELS[method]} thin crops (<10 districts): {thin.get('crop_count', 0)} crops; "
              f"MAE={_format(thin.get('mae_kg_ha'), 1)} kg/ha, "
              f"MAE%={_format(thin.get('mae_pct_crop_mean'), 1)}, "
              f"RMSE={_format(thin.get('rmse_kg_ha'), 1)}, "
              f"Spearman={_format(thin.get('spearman_rank_correlation'))}, "
              f"top-6 overlap={_format(thin.get('top6_overlap_share'))}")
        thin_crops = [crop for crop in result[method].get("per_crop", []) if crop["thin"]]
        if thin_crops:
            print("    Thin-crop scores: crop | districts | n | MAE kg/ha | MAE % mean | RMSE | within R² | Spearman | top-6 overlap")
            for crop in thin_crops:
                print("    " + " | ".join([
                    crop["crop"], str(crop["district_count"]), str(crop["n"]),
                    _format(crop["mae_kg_ha"], 1), _format(crop["mae_pct_crop_mean"], 1),
                    _format(crop["rmse_kg_ha"], 1), _format(crop["within_crop_r2"]),
                    _format(crop["spearman_rank_correlation"]), _format(crop["top6_overlap_share"]),
                ]))
    if split_info.get("notes"):
        for note in split_info["notes"]:
            print(f"  Note: {note}")


def evaluate(input_path: Path, output_path: Path, prediction_path: Path) -> dict[str, Any]:
    random.seed(42)
    np.random.seed(42)
    if not input_path.is_file():
        raise FileNotFoundError(f"Training table not found: {input_path}")
    raw = pd.read_csv(input_path)
    result = grouped_oof_predictions(raw)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_path.parent.mkdir(parents=True, exist_ok=True)

    split_results = {}
    prediction_rows = []
    for split_name, rows in result["predictions"].items():
        requested = sum(1 for row in rows)
        method_results = evaluate_predictions(rows, requested)
        split_results[split_name] = {
            "split": result["splits"][split_name],
            "metrics": method_results,
        }
        prediction_rows.extend(rows)
        print_table(split_name, method_results, result["splits"][split_name])

    if prediction_rows:
        pd.DataFrame(prediction_rows).to_csv(prediction_path, index=False, na_rep="")
    else:
        pd.DataFrame(columns=["split", "fold", "season", "district", "crop", "actual_yield_kg_ha", *METHODS]).to_csv(prediction_path, index=False)

    report = {
        "schema_version": 1,
        "input": {
            "path": str(input_path.resolve()),
            "sha256": _sha256(input_path),
            "source_rows": int(len(raw)),
            "valid_target_rows": result["valid_rows"],
            "excluded_rows": int(len(raw) - result["valid_rows"]),
            "distinct_districts": int(raw["district"].nunique()) if "district" in raw else None,
            "distinct_crops": int(raw["crop"].nunique()) if "crop" in raw else None,
            "season_groups": result["season_groups"],
            "source_district_counts_by_crop": result["source_district_counts"],
        },
        "reproducibility": {
            "random_seed": 42,
            "randomness_used": False,
            "versions": runtime_versions(),
            "method_definitions": {
                "crop_mean": "Arithmetic mean yield_kg_ha for crop in training fold, ignoring district and season.",
                "crop_season_mean": "Arithmetic mean yield_kg_ha for crop and season_code in training fold.",
                "district_crop_season_weighted": "Sum(production_mt * 1000) / sum(harvested_area_ha) for district/crop/season_code in training fold; missing value falls back to training-fold crop mean.",
                "previous_season_same_district_crop": "Previous chronological season for same district/crop from training fold only; unavailable values remain missing.",
                "rank_metrics": "Spearman and top-6 overlap are computed within fold/crop/season groups; top-six denominator is min(6, observed district count). Leave-one-district-out rankings are unavailable because each held-out fold contains only one district.",
                "within_crop_metrics": "Compute metrics per crop and macro-average; centered R-squared subtracts the held-out crop's actual mean from actual and predicted values.",
            },
        },
        "splits": split_results,
        "artifacts": {
            "predictions_csv": str(prediction_path.resolve()),
        },
    }
    with output_path.open("w", encoding="utf-8") as stream:
        json.dump(_json_safe(report), stream, indent=2, ensure_ascii=False, allow_nan=False)
    print(f"Runtime versions: {json.dumps(report['reproducibility']['versions'], sort_keys=True)}")
    print(f"\nSaved grouped baseline evaluation: {output_path}")
    print(f"Saved out-of-fold predictions: {prediction_path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--predictions-output", type=Path, default=DEFAULT_OUTPUT.with_name("baseline_predictions.csv"))
    args = parser.parse_args()
    evaluate(args.input, args.output, args.predictions_output)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"BASELINE EVALUATION FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
