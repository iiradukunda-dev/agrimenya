"""Grouped out-of-fold evaluation utilities for yield baselines."""
from __future__ import annotations

import platform
from typing import Any

import numpy as np
import pandas as pd

METHODS = (
    "crop_mean",
    "crop_season_mean",
    "district_crop_season_weighted",
    "previous_season_same_district_crop",
)
REQUIRED_COLUMNS = {
    "district", "crop", "season_code", "year", "yield_kg_ha",
    "production_mt", "harvested_area_ha",
}
SEASON_ORDER = {"A": 0, "B": 1, "C": 2}


def _valid_rows(frame: pd.DataFrame) -> pd.DataFrame:
    missing = REQUIRED_COLUMNS.difference(frame.columns)
    if missing:
        raise ValueError(f"Training table is missing required columns: {', '.join(sorted(missing))}")
    data = frame.copy()
    for col in ("yield_kg_ha", "production_mt", "harvested_area_ha", "year"):
        data[col] = pd.to_numeric(data[col], errors="coerce")
    data["season_code"] = data["season_code"].astype("string").str.strip().str.upper()
    data["district"] = data["district"].astype("string").str.strip()
    data["crop"] = data["crop"].astype("string").str.strip()
    return data[
        data["district"].notna() & data["crop"].notna()
        & data["season_code"].isin(SEASON_ORDER)
        & data["year"].notna() & data["yield_kg_ha"].notna()
        & np.isfinite(data["yield_kg_ha"])
    ].copy()


def _previous_season_code(year: int, code: str) -> tuple[int, str]:
    order = SEASON_ORDER[code] - 1
    if order < 0:
        return year - 1, "C"
    return year, ("A", "B", "C")[order]


def _training_lookups(training: pd.DataFrame) -> dict[str, dict]:
    y = training[training["yield_kg_ha"].notna()]
    crop_mean = y.groupby("crop")["yield_kg_ha"].mean().to_dict()
    crop_season_mean = y.groupby(["crop", "season_code"])["yield_kg_ha"].mean().to_dict()

    weighted = {}
    valid_weight = y[
        y["harvested_area_ha"].gt(0)
        & y["production_mt"].ge(0)
        & y["harvested_area_ha"].notna()
        & y["production_mt"].notna()
    ]
    for (district, crop, code), rows in valid_weight.groupby(["district", "crop", "season_code"], sort=False):
        area = rows["harvested_area_ha"].sum()
        if area > 0:
            weighted[(str(district), str(crop), str(code))] = rows["production_mt"].sum() * 1000.0 / area

    previous = {}
    for (district, crop, year, code), rows in y.groupby(["district", "crop", "year", "season_code"], sort=False):
        year = int(year)
        key = (str(district), str(crop), year, str(code))
        previous[key] = float(rows["yield_kg_ha"].mean())
    return {
        "crop_mean": crop_mean,
        "crop_season_mean": crop_season_mean,
        "district_crop_season_weighted": weighted,
        "previous_season": previous,
    }


def _predict_fold(training: pd.DataFrame, testing: pd.DataFrame, split_name: str, fold: str) -> list[dict[str, Any]]:
    lookups = _training_lookups(training)
    results = []
    for _, row in testing.iterrows():
        district, crop, code = str(row["district"]), str(row["crop"]), str(row["season_code"])
        year = int(row["year"])
        crop_value = lookups["crop_mean"].get(crop)
        crop_season_value = lookups["crop_season_mean"].get((crop, code))
        district_value = lookups["district_crop_season_weighted"].get((district, crop, code), crop_value)
        previous_year, previous_code = _previous_season_code(year, code)
        previous_value = lookups["previous_season"].get((district, crop, previous_year, previous_code))
        prediction = {
            "split": split_name,
            "fold": fold,
            "season": str(row.get("season", f"{year} Season {code}")),
            "season_code": code,
            "year": year,
            "district": district,
            "crop": crop,
            "actual_yield_kg_ha": float(row["yield_kg_ha"]),
            "crop_mean": crop_value,
            "crop_season_mean": crop_season_value,
            "district_crop_season_weighted": district_value,
            "previous_season_same_district_crop": previous_value,
        }
        results.append(prediction)
    return results


def grouped_oof_predictions(frame: pd.DataFrame) -> dict[str, Any]:
    """Generate leave-one-district-out and leave-one-season-out predictions."""
    data = _valid_rows(frame).reset_index(drop=True)
    if data.empty:
        raise ValueError("No rows with valid district/crop/season/year/yield values")
    predictions: dict[str, list[dict[str, Any]]] = {"leave_one_district_out": [], "leave_one_season_out": []}
    split_info: dict[str, dict[str, Any]] = {}

    districts = sorted(data["district"].dropna().astype(str).unique())
    district_folds = 0
    district_reasons = []
    if len(districts) < 2:
        district_reasons.append(f"Need at least two districts; found {len(districts)}")
    else:
        for district in districts:
            testing = data[data["district"].astype(str) == district]
            training = data[data["district"].astype(str) != district]
            if training.empty or testing.empty:
                district_reasons.append(f"Skipped district {district}: empty train/test fold")
                continue
            predictions["leave_one_district_out"].extend(
                _predict_fold(training, testing, "leave_one_district_out", district)
            )
            district_folds += 1
    split_info["leave_one_district_out"] = {
        "folds_run": district_folds,
        "groups": len(districts),
        "status": "complete" if district_folds == len(districts) else "partial_or_unavailable",
        "notes": district_reasons + ["Per-fold district ranking metrics are not estimable: each fold holds out one district."],
    }

    data["season_group"] = data.apply(lambda row: f"{int(row['year'])} Season {row['season_code']}", axis=1)
    seasons = sorted(data["season_group"].unique())
    season_folds = 0
    season_reasons = []
    if len(seasons) < 2:
        season_reasons.append(f"Need at least two distinct year/season groups; found {len(seasons)}")
    else:
        for season in seasons:
            testing = data[data["season_group"] == season]
            training = data[data["season_group"] != season]
            if training.empty or testing.empty:
                season_reasons.append(f"Skipped {season}: empty train/test fold")
                continue
            predictions["leave_one_season_out"].extend(
                _predict_fold(training, testing, "leave_one_season_out", season)
            )
            season_folds += 1
    split_info["leave_one_season_out"] = {
        "folds_run": season_folds,
        "groups": len(seasons),
        "status": "complete" if season_folds == len(seasons) else "partial_or_unavailable",
        "notes": season_reasons,
    }
    source_counts = data.groupby("crop")["district"].nunique().to_dict()
    for rows in predictions.values():
        for row in rows:
            row["source_district_count"] = int(source_counts[row["crop"]])
    return {"predictions": predictions, "splits": split_info, "valid_rows": len(data), "season_groups": seasons,
            "source_district_counts": {str(crop): int(count) for crop, count in source_counts.items()}}


def _r2(actual: np.ndarray, predicted: np.ndarray) -> float | None:
    if len(actual) < 2:
        return None
    denominator = float(np.square(actual - actual.mean()).sum())
    if denominator == 0:
        return None
    return float(1.0 - np.square(actual - predicted).sum() / denominator)


def _spearman(actual: pd.Series, predicted: pd.Series) -> float | None:
    if len(actual) < 2:
        return None
    a = actual.rank(method="average")
    p = predicted.rank(method="average")
    if a.nunique() < 2 or p.nunique() < 2:
        return None
    value = a.corr(p, method="pearson")
    return float(value) if pd.notna(value) else None


def _rank_metrics(frame: pd.DataFrame, prediction_column: str) -> dict[str, Any]:
    correlations = []
    overlaps = []
    group_keys = ["crop", "season"]
    if "fold" in frame.columns:
        # LODO has one test district per fold, so a district ranking cannot
        # be evaluated within that fold; do not rank forecasts from different
        # fitted folds against one another.
        group_keys.insert(0, "fold")
    groups = frame.groupby(group_keys, sort=False)
    for _, group in groups:
        group = group.dropna(subset=[prediction_column, "actual_yield_kg_ha"])
        # A district must occur once per crop/season ranking.
        group = group.sort_values("district").drop_duplicates("district", keep="last")
        if len(group) < 2:
            continue
        rho = _spearman(group["actual_yield_kg_ha"], group[prediction_column])
        if rho is not None:
            correlations.append(rho)
        k = min(6, len(group))
        actual_top = set(group.nlargest(k, "actual_yield_kg_ha")["district"])
        predicted_top = set(group.nlargest(k, prediction_column)["district"])
        overlaps.append(len(actual_top & predicted_top) / k if k else None)
    return {
        "spearman_rank_correlation": float(np.mean(correlations)) if correlations else None,
        "top6_overlap_share": float(np.mean(overlaps)) if overlaps else None,
        "rank_groups": len(correlations),
    }


def _metrics(frame: pd.DataFrame, prediction_column: str) -> dict[str, Any]:
    if frame.empty:
        return {"n": 0, "coverage": 0.0, "mae_kg_ha": None, "mae_pct_crop_mean": None,
                "rmse_kg_ha": None, "r2": None, "within_crop": {},
                "spearman_rank_correlation": None, "top6_overlap_share": None,
                "rank_groups": 0, "per_crop": [], "thin_crop_summary": {}}
    valid = frame.dropna(subset=["actual_yield_kg_ha", prediction_column]).copy()
    if valid.empty:
        return {"n": 0, "coverage": 0.0, "mae_kg_ha": None, "mae_pct_crop_mean": None,
                "rmse_kg_ha": None, "r2": None, "within_crop": {}, **_rank_metrics(valid, prediction_column)}
    actual = valid["actual_yield_kg_ha"].to_numpy(dtype=float)
    predicted = valid[prediction_column].to_numpy(dtype=float)
    errors = predicted - actual
    crop_means = valid.groupby("crop")["actual_yield_kg_ha"].transform("mean").to_numpy(dtype=float)
    centered_actual = actual - crop_means
    centered_predicted = predicted - crop_means

    by_crop = []
    for crop, group in valid.groupby("crop", sort=True):
        y = group["actual_yield_kg_ha"].to_numpy(dtype=float)
        p = group[prediction_column].to_numpy(dtype=float)
        crop_mean = float(y.mean())
        crop_mae = float(np.abs(p - y).mean())
        crop_rmse = float(np.sqrt(np.square(p - y).mean()))
        centered_y = y - crop_mean
        centered_p = p - crop_mean
        rank_frame = group.copy()
        by_crop.append({
            "crop": str(crop),
            "district_count": int(group["source_district_count"].iloc[0]) if "source_district_count" in group else int(group["district"].nunique()),
            "evaluated_district_count": int(group["district"].nunique()),
            "thin": (int(group["source_district_count"].iloc[0]) if "source_district_count" in group else int(group["district"].nunique())) < 10,
            "n": int(len(group)),
            "crop_mean_yield_kg_ha": crop_mean,
            "mae_kg_ha": crop_mae,
            "mae_pct_crop_mean": crop_mae / abs(crop_mean) * 100 if crop_mean else None,
            "rmse_kg_ha": crop_rmse,
            "within_crop_r2": _r2(centered_y, centered_p),
            **_rank_metrics(rank_frame, prediction_column),
        })
    rank = _rank_metrics(valid, prediction_column)
    macro = lambda key: float(np.mean([x[key] for x in by_crop if x[key] is not None])) if any(x[key] is not None for x in by_crop) else None
    mean_pct = float(np.mean([x["mae_pct_crop_mean"] for x in by_crop if x["mae_pct_crop_mean"] is not None])) if any(x["mae_pct_crop_mean"] is not None for x in by_crop) else None
    return {
        "n": int(len(valid)),
        "coverage": float(len(valid) / len(frame)) if len(frame) else 0.0,
        "mae_kg_ha": float(np.abs(errors).mean()),
        "mae_pct_crop_mean": mean_pct,
        "rmse_kg_ha": float(np.sqrt(np.square(errors).mean())),
        "r2": _r2(actual, predicted),
        "within_crop": {
            "macro_mae_kg_ha": macro("mae_kg_ha"),
            "macro_mae_pct_crop_mean": mean_pct,
            "macro_rmse_kg_ha": macro("rmse_kg_ha"),
            "centered_r2": _r2(centered_actual, centered_predicted),
        },
        **rank,
        "per_crop": by_crop,
        "thin_crop_summary": {
            "crop_count": sum(1 for row in by_crop if row["thin"]),
            "mae_kg_ha": float(np.mean([x["mae_kg_ha"] for x in by_crop if x["thin"]])) if any(x["thin"] for x in by_crop) else None,
            "mae_pct_crop_mean": float(np.mean([x["mae_pct_crop_mean"] for x in by_crop if x["thin"] and x["mae_pct_crop_mean"] is not None])) if any(x["thin"] and x["mae_pct_crop_mean"] is not None for x in by_crop) else None,
            "rmse_kg_ha": float(np.mean([x["rmse_kg_ha"] for x in by_crop if x["thin"]])) if any(x["thin"] for x in by_crop) else None,
            "spearman_rank_correlation": float(np.mean([x["spearman_rank_correlation"] for x in by_crop if x["thin"] and x["spearman_rank_correlation"] is not None])) if any(x["thin"] and x["spearman_rank_correlation"] is not None for x in by_crop) else None,
            "top6_overlap_share": float(np.mean([x["top6_overlap_share"] for x in by_crop if x["thin"] and x["top6_overlap_share"] is not None])) if any(x["thin"] and x["top6_overlap_share"] is not None for x in by_crop) else None,
        },
    }


def evaluate_predictions(predictions: list[dict[str, Any]], requested_rows: int) -> dict[str, Any]:
    frame = pd.DataFrame(predictions)
    if frame.empty:
        return {method: _metrics(frame, method) for method in METHODS}
    result = {}
    for method in METHODS:
        result[method] = _metrics(frame, method)
        result[method]["requested_rows"] = int(requested_rows)
    return result


def runtime_versions() -> dict[str, str]:
    versions = {"python": platform.python_version(), "pandas": pd.__version__, "numpy": np.__version__}
    try:
        import scipy
        versions["scipy"] = scipy.__version__
    except ImportError:
        versions["scipy"] = "not installed (not required; pandas rank correlation used)"
    return versions
