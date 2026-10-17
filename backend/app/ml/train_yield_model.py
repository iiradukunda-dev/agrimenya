"""Grouped comparison of yield models and fold-safe conformal intervals.

Run from ``backend`` with ``python -m app.ml.train_yield_model``. The fixed
candidate settings below are declared before evaluation; there is no tuning on
the evaluation folds. No random row split is used.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
try:
    from xgboost import XGBRegressor
except ImportError as exc:
    raise SystemExit("XGBoost is required for the grouped early-stopping candidate; install backend requirements.") from exc

from app.ml.features import build_features
from app.ml.intervals import conformal_quantile
from app.ml.validation import METHODS, _metrics, _valid_rows, evaluate_predictions, grouped_oof_predictions, runtime_versions

BACKEND = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = BACKEND / "data" / "training_table.csv"
BASELINE_REPORT = BACKEND / "data" / "eval" / "baselines.json"
EVAL_DIR = BACKEND / "data" / "eval"
ARTIFACT_DIR = BACKEND / "app" / "ml" / "artifacts"
SEED = 42
NOMINAL_INTERVAL = 0.80
MIN_CROP_DISTRICTS = 10

# Fixed, intentionally small model configurations. Hyperparameters are not
# selected from the final evaluation folds.
RIDGE_ALPHA = 10.0
BOOSTING_CONFIG = {"n_estimators": 300, "max_depth": 3, "learning_rate": 0.03,
                   "min_child_weight": 10, "reg_alpha": 2.0, "reg_lambda": 10.0,
                   "subsample": 0.8, "colsample_bytree": 0.8, "early_stopping_rounds": 15}
DECISION_MAE_MARGIN = 0.05
DECISION_SPEARMAN_MARGIN = 0.05

BASELINE_METHODS = METHODS
CANDIDATES = ("ridge_log_yield", "gradient_boosting_log_yield", "mixed_effects_shrinkage")
LABELS = {
    "crop_mean": "Crop mean", "crop_season_mean": "Crop x season-code mean",
    "district_crop_season_weighted": "District-crop-season weighted; crop fallback",
    "previous_season_same_district_crop": "Previous-season district-crop",
    "ridge_log_yield": "Ridge log-yield + crop FE",
    "gradient_boosting_log_yield": "Shallow gradient boosting",
    "mixed_effects_shrinkage": "Crop + district-within-crop shrinkage",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _versions() -> dict[str, str]:
    from importlib.metadata import PackageNotFoundError, version
    result = {**runtime_versions(), "python": platform.python_version()}
    for package in ("scikit-learn", "xgboost"):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "not installed"
    return result


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "item"):
        return _json_safe(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def _features(frame: pd.DataFrame, categories: dict[str, list[str]] | None = None) -> pd.DataFrame:
    # The configured feature builder excludes target-derived columns and keeps
    # NISR-sourced district/season context. Category vocabularies are fold-local.
    result = build_features(frame, known_categories=categories)
    for column in result.select_dtypes(include=["string", "object"]).columns:
        result[column] = result[column].astype(object).where(result[column].notna(), np.nan)
    return result


def _make_model(kind: str, training_features: pd.DataFrame):
    categorical = [c for c in ("district", "crop", "crop_category", "season_code") if c in training_features]
    numeric = [c for c in training_features if c not in categorical]
    transformers = []
    if categorical:
        transformers.append(("categorical", Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]), categorical))
    if numeric:
        numeric_steps = [("imputer", SimpleImputer(strategy="median"))]
        if kind == "ridge_log_yield":
            numeric_steps.append(("scale", StandardScaler(with_mean=False)))
        transformers.append(("numeric", Pipeline(numeric_steps), numeric))
    # Dense one-hot output is modest at this dataset size and is required by
    # sklearn's histogram booster. Ridge's LSQR solver also accepts it.
    transform = ColumnTransformer(transformers, remainder="drop", sparse_threshold=0.0)
    if kind == "ridge_log_yield":
        estimator = Ridge(alpha=RIDGE_ALPHA, solver="lsqr")
    else:
        estimator = XGBRegressor(objective="reg:squarederror", eval_metric="mae",
                                 random_state=SEED, n_jobs=1, **BOOSTING_CONFIG)
    return Pipeline([("features", transform), ("model", estimator)])


def _shrinkage_predict(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """Crop fixed effect plus empirical-Bayes district intercept (log scale)."""
    logs = np.log(train["yield_kg_ha"].to_numpy(dtype=float))
    work = train[["crop", "district"]].copy()
    work["log_y"] = logs
    crop_mean = work.groupby("crop")["log_y"].mean()
    residual = work["log_y"] - work["crop"].map(crop_mean)
    residual_frame = work.assign(residual=residual)
    district_residual = residual_frame.groupby(["crop", "district"])["residual"].agg(["mean", "count"])
    # Fixed, conservative prior equivalent to ten district observations.
    strength = 10.0
    correction = district_residual["mean"] * district_residual["count"] / (district_residual["count"] + strength)
    result = []
    for row in test.itertuples(index=False):
        base = crop_mean.get(row.crop, float(np.mean(logs)))
        result.append(float(base + correction.get((row.crop, row.district), 0.0)))
    return np.exp(np.asarray(result))


def _candidate_predictions(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, np.ndarray]:
    valid_train = train[train["yield_kg_ha"].gt(0)].copy()
    valid_test = test.copy()
    if valid_train.empty:
        raise ValueError("A training fold has no positive yield values")
    cats = {name: sorted(valid_train[name].dropna().astype(str).unique())
            for name in ("district", "crop", "crop_category", "season_code") if name in valid_train}
    x_train, x_test = _features(valid_train, cats), _features(valid_test, cats)
    y_train = np.log(valid_train["yield_kg_ha"].astype(float))
    predictions: dict[str, np.ndarray] = {}
    for kind in ("ridge_log_yield", "gradient_boosting_log_yield"):
        model = _make_model(kind, x_train)
        if kind == "gradient_boosting_log_yield":
            # Internal validation holds out entire districts from this outer
            # training fold, preserving the no-row-random-split rule.
            validation_district = sorted(valid_train["district"].astype(str).unique())[-1]
            inner_train = valid_train[valid_train["district"].astype(str) != validation_district]
            inner_valid = valid_train[valid_train["district"].astype(str) == validation_district]
            inner_x = _features(inner_train, cats)
            inner_v = _features(inner_valid, cats)
            transformer = model.named_steps["features"]
            inner_x_transformed = transformer.fit_transform(inner_x)
            inner_v_transformed = transformer.transform(inner_v)
            model.named_steps["model"].fit(
                inner_x_transformed, np.log(inner_train["yield_kg_ha"].astype(float)),
                eval_set=[(inner_v_transformed, np.log(inner_valid["yield_kg_ha"].astype(float)))],
                verbose=False)
            # Refit with the selected tree count on the complete outer fold.
            best_round = max(1, int(model.named_steps["model"].best_iteration) + 1)
            model = _make_model(kind, x_train)
            model.named_steps["model"].set_params(n_estimators=best_round, early_stopping_rounds=None)
            model.fit(x_train, y_train)
        else:
            model.fit(x_train, y_train)
        predictions[kind] = np.exp(model.predict(x_test))
    predictions["mixed_effects_shrinkage"] = _shrinkage_predict(valid_train, valid_test)
    return predictions


def _all_oof(frame: pd.DataFrame) -> dict[str, Any]:
    """Run both M5 split families and append three candidates per held-out row."""
    grouped = grouped_oof_predictions(frame)
    category_by_crop = frame.drop_duplicates("crop").set_index("crop")["crop_category"].to_dict()
    for split_name, rows in grouped["predictions"].items():
        by_fold: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            by_fold.setdefault(row["fold"], []).append(row)
        for fold, fold_rows in by_fold.items():
            for row in fold_rows:
                row["crop_category"] = category_by_crop.get(row["crop"])
            if split_name == "leave_one_district_out":
                training = frame[frame["district"].astype(str) != fold]
            else:
                training = frame[frame.apply(lambda r: f"{int(r['year'])} Season {r['season_code']}" != fold, axis=1)]
            testing_keys = {(r["district"], r["crop"], r["season_code"], int(r["year"])) for r in fold_rows}
            testing = frame[[
                (str(r.district), str(r.crop), str(r.season_code), int(r.year)) in testing_keys
                for r in frame.itertuples()
            ]].copy()
            # M5 input is one district/crop/season/year per key; preserve exactly
            # the validation module's held-out rows/order.
            lookup = {(str(r.district), str(r.crop), str(r.season_code), int(r.year)): i
                      for i, r in zip(testing.index, testing.itertuples())}
            ordered_indices = [lookup[(r["district"], r["crop"], r["season_code"], int(r["year"]))] for r in fold_rows]
            testing = frame.loc[ordered_indices].reset_index(drop=True)
            preds = _candidate_predictions(training, testing)
            for index, row in enumerate(fold_rows):
                for method, values in preds.items():
                    row[method] = float(values[index])
    return grouped


def _append_candidate_metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    result = evaluate_predictions(rows, len(rows))
    frame = pd.DataFrame(rows)
    for method in CANDIDATES:
        result[method] = _metrics(frame, method)
    # M5's helper intentionally avoids rankings for LODO because it ranks each
    # one-district fold. Aggregate OOF rows by crop/season to estimate within-
    # crop rank quality without mixing predictions from a shared fitted fold.
    for method in list(METHODS) + list(CANDIDATES):
        correlations = []
        for _, group in frame.groupby(["crop", "season"], sort=False):
            if group[method].notna().sum() >= 2:
                rho = group[["actual_yield_kg_ha", method]].corr(method="spearman").iloc[0, 1]
                if pd.notna(rho):
                    correlations.append(float(rho))
        result[method]["spearman_rank_correlation"] = float(np.mean(correlations)) if correlations else None
    return result


def _print_table(split: str, rows: list[dict[str, Any]], split_info: dict[str, Any]) -> dict[str, Any]:
    metrics = _append_candidate_metrics(rows)
    print(f"\n{split.replace('_', ' ').title()} — {split_info['folds_run']}/{split_info['groups']} folds ({split_info['status']})")
    headers = ["Method", "N", "Coverage", "MAE kg/ha", "MAE % mean", "RMSE", "Within MAE", "Within MAE %", "Within RMSE", "Within R²", "Spearman", "Top-6 overlap"]
    methods = list(METHODS) + list(CANDIDATES)
    matrix = []
    for method in methods:
        m = metrics[method]
        def fmt(value, digits=3):
            return "n/a" if value is None else f"{float(value):.{digits}f}"
        matrix.append([LABELS[method], str(m.get("n", 0)), fmt(m.get("coverage")), fmt(m.get("mae_kg_ha"), 1),
                       fmt(m.get("mae_pct_crop_mean"), 1), fmt(m.get("rmse_kg_ha"), 1),
                       fmt(m.get("within_crop", {}).get("macro_mae_kg_ha"), 1),
                       fmt(m.get("within_crop", {}).get("macro_mae_pct_crop_mean"), 1),
                       fmt(m.get("within_crop", {}).get("macro_rmse_kg_ha"), 1),
                       fmt(m.get("within_crop", {}).get("centered_r2")), fmt(m.get("spearman_rank_correlation")),
                       fmt(m.get("top6_overlap_share"))])
    widths = [max(len(headers[i]), *(len(row[i]) for row in matrix)) for i in range(len(headers))]
    print(" | ".join(headers[i].ljust(widths[i]) for i in range(len(headers))))
    print("-+-".join("-" * w for w in widths))
    for row in matrix:
        print(" | ".join(row[i].ljust(widths[i]) for i in range(len(row))))
    print("Within columns are macro averages across crops. LODO Spearman aggregates OOF districts within crop/season.")
    return metrics


def _conformal_quantile(scores: list[float], level: float) -> float:
    return conformal_quantile(scores, level)


def _calibrate(rows: list[dict[str, Any]], source_counts: dict[str, int], prediction_column: str) -> dict[str, Any]:
    # Absolute residual scores on log scale, generated only from held-out rows.
    scores_by_category: dict[str, list[float]] = {}
    global_scores = []
    for row in rows:
        pred = row.get(prediction_column)
        actual = row.get("actual_yield_kg_ha")
        if pred is None or pred <= 0 or actual <= 0:
            continue
        score = abs(float(np.log(actual)) - float(np.log(pred)))
        category = str(row.get("crop_category") or "Unknown")
        scores_by_category.setdefault(category, []).append(score)
        global_scores.append(score)
    global_q = _conformal_quantile(global_scores, NOMINAL_INTERVAL)
    categories = {}
    for category, scores in scores_by_category.items():
        categories[category] = {"count": len(scores), "quantile_log": max(global_q, _conformal_quantile(scores, NOMINAL_INTERVAL))}
    return {"interval_level": NOMINAL_INTERVAL, "prediction_column": prediction_column,
            "global_quantile_log": global_q,
            "by_crop_category": categories, "source_district_counts": source_counts,
            "crop_category_by_crop": {str(row["crop"]): str(row["crop_category"])
                                      for row in rows if row.get("crop") and row.get("crop_category")},
            "minimum_districts": MIN_CROP_DISTRICTS,
            "thin_crop_rule": "Use at least global conformal width; mark insufficient_data when the crop has fewer than 10 source districts."}


def _print_calibration(rows: list[dict[str, Any]], calibration: dict[str, Any]) -> dict[str, Any]:
    prediction_column = calibration.get("prediction_column", "ridge_log_yield")
    print(f"\nSplit-conformal calibration (nominal {NOMINAL_INTERVAL:.0%}, log-yield, OOF {prediction_column})")
    print("Scope | N | Coverage | Mean width (kg/ha)")
    data = []
    for row in rows:
        actual, pred = row.get("actual_yield_kg_ha"), row.get(prediction_column)
        if actual is None or pred is None or actual <= 0 or pred <= 0:
            continue
        category = str(row.get("crop_category") or "Unknown")
        q = calibration["by_crop_category"].get(category, {}).get("quantile_log", calibration["global_quantile_log"])
        data.append((category, float(actual), float(pred), float(q)))
    table = {}
    for category in ["Overall", *sorted({r[0] for r in data})]:
        selected = data if category == "Overall" else [r for r in data if r[0] == category]
        if not selected:
            continue
        coverage = np.mean([np.exp(np.log(p) - q) <= y <= np.exp(np.log(p) + q) for _, y, p, q in selected])
        width = np.mean([np.exp(np.log(p) + q) - np.exp(np.log(p) - q) for _, _, p, q in selected])
        table[category] = {"n": len(selected), "empirical_coverage": float(coverage),
                           "mean_width_kg_ha": float(width), "nominal_coverage": NOMINAL_INTERVAL}
        print(f"{category} | {len(selected)} | {coverage:.3f} | {width:.1f}")
    return table


def _decision(split_metrics: dict[str, dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    """Require >=5% macro-MAE improvement and >=.05 Spearman gain on both splits."""
    decision = {}
    for split_name, metrics in split_metrics.items():
        baselines = [metrics[name] for name in BASELINE_METHODS]
        baseline_mae = min((m["within_crop"].get("macro_mae_kg_ha") for m in baselines
                            if m["within_crop"].get("macro_mae_kg_ha") is not None), default=None)
        baseline_rho = max((m.get("spearman_rank_correlation") for m in baselines
                            if m.get("spearman_rank_correlation") is not None), default=None)
        candidates = []
        for name in CANDIDATES:
            m = metrics[name]
            mae, rho = m["within_crop"].get("macro_mae_kg_ha"), m.get("spearman_rank_correlation")
            passes = (baseline_mae is not None and baseline_rho is not None and mae is not None and rho is not None
                      and mae <= baseline_mae * (1 - DECISION_MAE_MARGIN)
                      and rho >= baseline_rho + DECISION_SPEARMAN_MARGIN)
            candidates.append((name, passes, mae, rho))
        decision[split_name] = {"best_baseline_within_crop_mae": baseline_mae,
                                "best_baseline_within_crop_spearman": baseline_rho,
                                "candidates": [{"name": n, "passes": p, "within_crop_mae": mae, "spearman": rho}
                                               for n, p, mae, rho in candidates]}
    pass_both = [name for name in CANDIDATES if all(any(c["name"] == name and c["passes"]
                   for c in decision[s]["candidates"]) for s in decision)]
    if not pass_both:
        return "KEEP BASELINE", decision
    # Fixed winner ordering: maximize LODO Spearman, then minimize LODO MAE.
    lodo = split_metrics["leave_one_district_out"]
    winner = max(pass_both, key=lambda n: (lodo[n].get("spearman_rank_correlation", -1),
                                           -lodo[n]["within_crop"].get("macro_mae_kg_ha", float("inf"))))
    return winner, decision


def train(input_path: Path = DEFAULT_INPUT, baseline_report: Path = BASELINE_REPORT) -> dict[str, Any]:
    np.random.seed(SEED)
    if not input_path.is_file():
        raise FileNotFoundError(f"NISR training table not found: {input_path}")
    frame = _valid_rows(pd.read_csv(input_path)).reset_index(drop=True)
    if frame["yield_kg_ha"].le(0).any():
        frame = frame[frame["yield_kg_ha"].gt(0)].reset_index(drop=True)
    if "crop_category" not in frame:
        raise ValueError("NISR training table is missing crop_category; categories cannot be invented")
    grouped = _all_oof(frame)
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    split_metrics = {}
    all_rows = []
    for name, rows in grouped["predictions"].items():
        split_metrics[name] = _print_table(name, rows, grouped["splits"][name])
        all_rows.extend(rows)
    oof_path = EVAL_DIR / "oof_predictions.csv"
    pd.DataFrame(all_rows).to_csv(oof_path, index=False, na_rep="")

    district_counts = frame.groupby("crop")["district"].nunique().astype(int).to_dict()
    winner, decision = _decision(split_metrics)
    calibration_column = "district_crop_season_weighted" if winner == "KEEP BASELINE" else winner
    calibration = _calibrate(grouped["predictions"]["leave_one_district_out"],
                             {str(k): int(v) for k, v in district_counts.items()}, calibration_column)
    calibration["training_date_utc"] = datetime.now(timezone.utc).isoformat()
    calibration["data_sha256"] = _sha256(input_path)
    calibration["versions"] = _versions()
    # Quantiles come only from LODO OOF residuals; report coverage on the
    # separate leave-one-season-out OOF predictions as a held-out calibration check.
    calibration_evaluation = _print_calibration(grouped["predictions"]["leave_one_season_out"], calibration)
    calibration_path = ARTIFACT_DIR / "yield_intervals.json"
    calibration_path.write_text(json.dumps(_json_safe(calibration), indent=2), encoding="utf-8")

    report = {"schema_version": 1, "winner": winner, "decision_rule": {
        "criterion": "candidate must beat the best baseline on both split types by at least 5% within-crop macro MAE and 0.05 within-crop Spearman; winner then maximizes LODO Spearman and minimizes LODO MAE",
        "mae_margin": DECISION_MAE_MARGIN, "spearman_margin": DECISION_SPEARMAN_MARGIN,
        "scores": decision}, "interval_calibration_prediction_column": calibration_column,
        "interval_calibration_evaluation": calibration_evaluation,
        "input": {"path": str(input_path.resolve()), "sha256": _sha256(input_path),
        "rows": len(frame), "districts": int(frame.district.nunique()), "crops": int(frame.crop.nunique())},
        "training_data_span": {"seasons": sorted(frame["season"].dropna().astype(str).unique().tolist())
                               if "season" in frame else sorted(frame["season_code"].dropna().astype(str).unique().tolist())},
        "known_limitations": ["District-level survey associations do not establish causation.",
                              "Predictions are limited to the NISR seasons and crop categories represented in training data."],
        "training_date_utc": datetime.now(timezone.utc).isoformat(), "random_seed": SEED,
        "versions": _versions(),
        "feature_list": _features(frame).columns.tolist(), "splits": split_metrics,
        "artifacts": {"oof_predictions": str(oof_path.resolve()), "interval_calibration": str(calibration_path.resolve())}}

    report_path = EVAL_DIR / "yield_model_evaluation.json"
    report["artifacts"]["evaluation_report"] = str(report_path.resolve())
    report_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")

    model_path = ARTIFACT_DIR / "yield_model.pkl"
    card_path = ARTIFACT_DIR / "model_card.json"
    if winner == "KEEP BASELINE":
        print("\nKEEP BASELINE — no candidate clears both margins on both grouped split types; yield_model.pkl was not written.")
        if model_path.exists() or card_path.exists():
            retired = ARTIFACT_DIR / "archive" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            retired.mkdir(parents=True, exist_ok=False)
            if model_path.exists():
                model_path.replace(retired / model_path.name)
            if card_path.exists():
                card_path.replace(retired / card_path.name)
            print(f"Retired prior model artifacts to {retired}; baseline remains active.")
    else:
        cats = {name: sorted(frame[name].dropna().astype(str).unique())
                for name in ("district", "crop", "crop_category", "season_code") if name in frame}
        features = _features(frame, cats)
        if winner == "mixed_effects_shrinkage":
            # Persist a compact serving-time empirical Bayes specification.
            import pickle
            logs = np.log(frame.yield_kg_ha.astype(float))
            work = frame[["crop", "district"]].copy(); work["log_y"] = logs
            crop_means = work.groupby("crop").log_y.mean().to_dict()
            residuals = work.assign(residual=work.log_y - work.crop.map(crop_means))
            bundle_model = {"kind": winner, "crop_log_means": crop_means,
                            "district_corrections": {f"{c}|{d}": float(g.residual.mean() * len(g) / (len(g) + 10.0))
                                                     for (c, d), g in residuals.groupby(["crop", "district"])}}
        else:
            fitted = _make_model(winner, features)
            fitted.fit(features, np.log(frame.yield_kg_ha.astype(float)))
            bundle_model = fitted
        import pickle
        bundle = {"feature_schema_version": 2, "model_version": f"{winner}-nisr-grouped-v1",
                  "model_kind": winner, "model": bundle_model, "feature_list": features.columns.tolist(),
                  "known_categories": cats, "target_transform": "natural_log_yield_kg_ha",
                  "crop_categories": {str(c): str(g.crop_category.iloc[0]) for c, g in frame.groupby("crop")},
                  "interval_calibration": calibration}
        with model_path.open("wb") as stream:
            pickle.dump(bundle, stream)
        report["model_version"] = bundle["model_version"]
        report["model_sha256"] = _sha256(model_path)
        card_path.write_text(json.dumps(_json_safe(report), indent=2), encoding="utf-8")
        print(f"\nWinner: {winner}. Saved model and model card under {ARTIFACT_DIR}.")
    print(f"Saved out-of-fold predictions: {oof_path}")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--baseline-report", type=Path, default=BASELINE_REPORT)
    args = parser.parse_args()
    train(args.input, args.baseline_report)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, pd.errors.ParserError) as exc:
        print(f"YIELD MODEL TRAINING FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
