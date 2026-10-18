"""Audited, staged season ingestion and conditional yield-model promotion.

Example: python -m scripts.add_new_season nisr_2027_season_a.pdf --year 2027 --season A
"""
from __future__ import annotations

import argparse
import json
import math
import pickle
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from app.ml import train_yield_model as trainer
from app.ml import predict as serving
from scripts import build_yield_baseline

ROOT = Path(__file__).resolve().parents[1]
TABLE_PATH = ROOT / "data" / "training_table.csv"
ARTIFACTS = ROOT / "app" / "ml" / "artifacts"


def _extract_pdf_season(pdf_path: Path, year: int, code: str) -> list[dict]:
    from scripts.build_training_table import extract_single_season
    return extract_single_season(pdf_path, year, code)


def _audit_pdf_season(csv_path: Path, pdf_path: Path, label: str, flags_path: Path) -> int:
    from scripts.audit_training_data import audit_new_season
    return audit_new_season(csv_path, pdf_path, label, flags_path)


def _within_crop_scores(frame: pd.DataFrame, prediction: str) -> tuple[float, float]:
    from scipy.stats import spearmanr
    maes, correlations = [], []
    for _, group in frame.groupby("crop"):
        valid = group[["yield_kg_ha", prediction]].apply(pd.to_numeric, errors="coerce").dropna()
        if valid.empty:
            continue
        maes.append(float((valid["yield_kg_ha"] - valid[prediction]).abs().mean()))
        if len(valid) > 1:
            rho = spearmanr(valid["yield_kg_ha"], valid[prediction]).statistic
            if np.isfinite(rho):
                correlations.append(float(rho))
    return (float(np.mean(maes)) if maes else math.inf,
            float(np.mean(correlations)) if correlations else float("nan"))


def _json_number(value: float) -> float | None:
    return float(value) if np.isfinite(value) else None


def _previous_model_predictions(bundle: dict | None, rows: pd.DataFrame, full: pd.DataFrame) -> list[float]:
    if bundle is None:
        values = []
        for row in rows.itertuples(index=False):
            value = serving._district_crop_baseline(str(row.district), str(row.crop), str(row.season))
            if value is None:
                value = serving.crop_mean(str(row.crop), str(row.season))
            values.append(float(value) if value is not None else float("nan"))
        return values
    result = []
    if bundle.get("model_kind") == "mixed_effects_shrinkage":
        model = bundle["model"]
        for row in rows.itertuples(index=False):
            log_y = model["crop_log_means"].get(row.crop)
            if log_y is None:
                result.append(float("nan"))
            else:
                correction = model["district_corrections"].get(f"{row.crop}|{row.district}", 0.0)
                result.append(math.exp(log_y + correction))
        return result
    features = trainer._features(rows, bundle.get("known_categories"))
    features = features.reindex(columns=bundle.get("feature_list", features.columns), fill_value=np.nan)
    return np.exp(bundle["model"].predict(features)).astype(float).tolist()


def _load_valid_deployed() -> dict | None:
    try:
        return serving.load_model_artifacts()
    except Exception as exc:
        print(f"Current model is not a valid deployed artifact; baseline comparison applies: {exc}")
        return None


def _compare_candidate(candidate: dict, deployed: dict | None, heldout: pd.DataFrame,
                       historical: pd.DataFrame, newest_season: str) -> tuple[bool, dict]:
    heldout = heldout.copy()
    method = candidate.get("model_kind")
    if heldout.empty or not method:
        raise RuntimeError(f"No independent {newest_season} holdout rows for candidate")
    heldout["candidate_prediction"] = _previous_model_predictions(candidate, heldout, historical)
    heldout["deployed_prediction"] = _previous_model_predictions(deployed, heldout, historical)
    heldout = heldout.dropna(subset=["yield_kg_ha", "candidate_prediction", "deployed_prediction"])
    if heldout.empty:
        raise RuntimeError("No common valid rows to compare candidate and deployed prediction")
    candidate_mae, candidate_rho = _within_crop_scores(heldout, "candidate_prediction")
    deployed_mae, deployed_rho = _within_crop_scores(heldout, "deployed_prediction")
    mae_margin = 0.05
    better = (candidate_mae <= deployed_mae * (1.0 - mae_margin) and np.isfinite(candidate_rho) and
              (not np.isfinite(deployed_rho) or candidate_rho >= deployed_rho))
    comparison = {"heldout_season": newest_season, "rows": len(heldout),
                  "candidate": method, "candidate_within_crop_mae": _json_number(candidate_mae),
                  "candidate_within_crop_spearman": _json_number(candidate_rho),
                  "deployed_within_crop_mae": _json_number(deployed_mae),
                  "deployed_within_crop_spearman": _json_number(deployed_rho),
                  "required_mae_improvement_fraction": mae_margin,
                  "decision": "PROMOTE" if better else "KEEP CURRENT"}
    print("Same held-out season comparison:")
    print(json.dumps(comparison, indent=2, allow_nan=False))
    return better, comparison


def _refit_selected_candidate(candidate: dict, full: pd.DataFrame) -> dict:
    """Refit the historically selected candidate after the new season holdout passes."""
    valid = trainer._valid_rows(full)
    categories = {name: sorted(valid[name].dropna().astype(str).unique())
                  for name in ("district", "crop", "crop_category", "season_code") if name in valid}
    features = trainer._features(valid, categories)
    kind = candidate["model_kind"]
    if kind == "mixed_effects_shrinkage":
        logs = np.log(valid.yield_kg_ha.astype(float))
        work = valid[["crop", "district"]].copy()
        work["log_y"] = logs
        crop_means = work.groupby("crop").log_y.mean().to_dict()
        residuals = work.assign(residual=work.log_y - work.crop.map(crop_means))
        model = {"kind": kind, "crop_log_means": crop_means,
                 "district_corrections": {
                     f"{crop}|{district}": float(group.residual.mean() * len(group) / (len(group) + 10.0))
                     for (crop, district), group in residuals.groupby(["crop", "district"])
                 }}
    else:
        model = trainer._make_model(kind, features)
        model.fit(features, np.log(valid.yield_kg_ha.astype(float)))
    result = dict(candidate)
    result.update({
        "model": model,
        "feature_list": features.columns.tolist(),
        "known_categories": categories,
        "crop_categories": {str(crop): str(group.crop_category.iloc[0])
                            for crop, group in valid.groupby("crop")},
    })
    return result


def _drift_report(full: pd.DataFrame, oof_path: Path, newest_season: str, model_kind: str) -> dict:
    current = full[full.season.astype(str) == newest_season]
    previous = full[full.season.astype(str) != newest_season]
    features = [column for column in full.select_dtypes(include=[np.number]).columns
                if column not in {"yield_kg_ha", "production_mt", "year", "n_districts_for_crop"}]
    shifts = []
    for feature in features:
        now = pd.to_numeric(current[feature], errors="coerce").dropna()
        before = pd.to_numeric(previous[feature], errors="coerce").dropna()
        if now.empty or before.empty:
            continue
        scale = float(before.std(ddof=1)) if len(before) > 1 else 0.0
        delta = abs(float(now.mean()) - float(before.mean()))
        shifts.append({"feature": feature, "newest_mean": float(now.mean()),
                       "previous_mean": float(before.mean()), "absolute_mean_shift": delta,
                       "standardized_shift": delta / scale if scale > 1e-12 else None})
    shifts.sort(key=lambda item: item["standardized_shift"] if item["standardized_shift"] is not None else -1,
                reverse=True)
    oof = pd.read_csv(oof_path)
    oof = oof[(oof.split == "leave_one_season_out") & (oof["fold"].astype(str) != "")]
    errors = {}
    if model_kind in oof:
        for season, group in oof.groupby("fold"):
            values = group[["yield_kg_ha", model_kind]].apply(pd.to_numeric, errors="coerce").dropna()
            errors[str(season)] = float((values.yield_kg_ha - values[model_kind]).abs().mean()) if len(values) else None
    print("Largest feature distribution shifts (absolute standardized mean shift):")
    for item in shifts[:10]:
        print(f"  {item['feature']}: {item['standardized_shift'] if item['standardized_shift'] is not None else 'NA'}")
    print("Leave-one-season-out candidate MAE by held-out season (kg/ha):")
    for season, value in errors.items():
        print(f"  {season}: {value}")
    return {"newest_season": newest_season, "feature_shifts": shifts,
            "leave_one_season_out_mae_kg_ha": errors}


def add_new_season(pdf_path: Path, year: int, season_code: str,
                   table_path: Path = TABLE_PATH) -> dict:
    season_code = season_code.upper()
    season_label = f"{year} Season {season_code}"
    if season_code not in {"A", "B", "C"} or year < 2000 or year > 2100:
        raise ValueError("Provide a valid season code A/B/C and year 2000-2100")
    if not pdf_path.is_file():
        raise FileNotFoundError(f"NISR season PDF not found: {pdf_path}")
    evaluation_archive = ROOT / "data" / "eval" / f"retrain_{year}_season_{season_code}"
    if evaluation_archive.exists():
        raise FileExistsError(f"Evaluation archive already exists: {evaluation_archive}")
    original = pd.read_csv(table_path)
    with tempfile.TemporaryDirectory(prefix="agrimenya-season-") as directory:
        stage = Path(directory)
        extracted_rows = _extract_pdf_season(pdf_path, year, season_code)
        extracted = pd.DataFrame(extracted_rows)
        extracted_path = stage / "extracted_season.csv"
        extracted.to_csv(extracted_path, index=False)
        audit_status = _audit_pdf_season(extracted_path, pdf_path, season_label, stage / "audit_flags.csv")
        if audit_status != 0:
            raise RuntimeError("Source audit failed; season data and model artifacts were not changed")

        combined = original.copy()
        for column in extracted.columns:
            if column not in combined:
                combined[column] = pd.NA
        for column in combined.columns:
            if column not in extracted:
                extracted[column] = pd.NA
        extracted = extracted.reindex(columns=combined.columns)
        keys = {(str(row.district).casefold(), str(row.crop).casefold(), str(row.season).casefold())
                for row in combined.itertuples()}
        duplicates = [row for row in extracted.itertuples()
                      if (str(row.district).casefold(), str(row.crop).casefold(), str(row.season).casefold()) in keys]
        if duplicates:
            raise ValueError(f"Season already contains {len(duplicates)} district/crop records")
        full = pd.concat([combined, extracted], ignore_index=True)
        full.to_csv(stage / "training_table.csv", index=False)
        historical_path = stage / "historical_training_table.csv"
        original.to_csv(historical_path, index=False)
        new_baselines = build_yield_baseline.build(full.fillna("").to_dict("records"))
        new_baselines["training_data_sha256"] = trainer._sha256(stage / "training_table.csv")
        baseline_stage = stage / "yield_baselines.json"
        baseline_stage.write_text(json.dumps(new_baselines, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")

        old_artifact_dir, old_eval_dir = trainer.ARTIFACT_DIR, trainer.EVAL_DIR
        candidate_dir, evaluation_dir = stage / "candidate_artifacts", stage / "evaluation"
        trainer.ARTIFACT_DIR, trainer.EVAL_DIR = candidate_dir, evaluation_dir
        try:
            # Candidate selection only sees seasons preceding this release.
            report = trainer.train(historical_path, trainer.BASELINE_REPORT)
        finally:
            trainer.ARTIFACT_DIR, trainer.EVAL_DIR = old_artifact_dir, old_eval_dir
        report.setdefault("input", {})["path"] = str(table_path.resolve())
        report["input"]["sha256"] = trainer._sha256(historical_path)
        report["artifacts"] = {"oof_predictions": "oof_predictions.csv",
                               "evaluation_report": "yield_model_evaluation.json"}
        report_path = evaluation_dir / "yield_model_evaluation.json"
        report_path.write_text(json.dumps(trainer._json_safe(report), indent=2), encoding="utf-8")
        if (candidate_dir / "model_card.json").is_file():
            card_path = candidate_dir / "model_card.json"
            card = json.loads(card_path.read_text(encoding="utf-8"))
            card.update(report)
            candidate_model_path = candidate_dir / "yield_model.pkl"
            card["model_sha256"] = trainer._sha256(candidate_model_path)
            report["model_sha256"] = card["model_sha256"]
            report["model_version"] = card.get("model_version")
            card_path.write_text(json.dumps(trainer._json_safe(card), indent=2), encoding="utf-8")
            report_path.write_text(json.dumps(trainer._json_safe(report), indent=2), encoding="utf-8")
        oof_path = evaluation_dir / "oof_predictions.csv"
        candidate_path = candidate_dir / "yield_model.pkl"
        deployed = _load_valid_deployed()
        promoted = False
        comparison = {"decision": "KEEP CURRENT", "reason": "training selected KEEP BASELINE"}
        model_kind = "district_crop_season_weighted"
        if report.get("winner") != "KEEP BASELINE" and candidate_path.is_file():
            with candidate_path.open("rb") as stream:
                candidate = pickle.load(stream)
            model_kind = candidate.get("model_kind") or model_kind
            promoted, comparison = _compare_candidate(candidate, deployed, extracted, original, season_label)
            if promoted:
                candidate = _refit_selected_candidate(candidate, full)
                with candidate_path.open("wb") as stream:
                    pickle.dump(candidate, stream)
                card_path = candidate_dir / "model_card.json"
                card = json.loads(card_path.read_text(encoding="utf-8"))
                card.update({
                    "input": {"path": str(table_path.resolve()),
                              "sha256": trainer._sha256(stage / "training_table.csv"),
                              "rows": len(full), "districts": int(full.district.nunique()),
                              "crops": int(full.crop.nunique())},
                    "training_data_span": {"seasons": sorted(full.season.dropna().astype(str).unique().tolist())},
                    "feature_list": candidate["feature_list"],
                    "training_date_utc": datetime.now(timezone.utc).isoformat(),
                    "model_sha256": trainer._sha256(candidate_path),
                    "promotion_holdout": comparison,
                })
                card["artifacts"] = {"promotion_holdout_season": season_label}
                card_path.write_text(json.dumps(trainer._json_safe(card), indent=2), encoding="utf-8")
                report.update({"input": card["input"], "training_data_span": card["training_data_span"],
                               "model_sha256": card["model_sha256"], "model_version": card.get("model_version"),
                               "promotion_holdout": comparison})
                report_path.write_text(json.dumps(trainer._json_safe(report), indent=2), encoding="utf-8")
        drift = _drift_report(full, oof_path, season_label, model_kind)

        # Commit source data and refreshed baseline only after audit and training complete.
        table_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_target = ARTIFACTS / "yield_baselines.json"
        table_temp = table_path.with_suffix(".csv.pending")
        baseline_temp = baseline_target.with_suffix(".json.pending")
        table_backup = table_path.with_suffix(".csv.rollback")
        baseline_backup = baseline_target.with_suffix(".json.rollback")
        shutil.copy2(stage / "training_table.csv", table_temp)
        shutil.copy2(baseline_stage, baseline_temp)
        shutil.copy2(table_path, table_backup)
        shutil.copy2(baseline_target, baseline_backup)
        try:
            table_temp.replace(table_path)
            baseline_temp.replace(baseline_target)
        except Exception:
            # Restore the prior consistent pair if either atomic rename fails.
            if table_backup.exists():
                table_backup.replace(table_path)
            if baseline_backup.exists():
                baseline_backup.replace(baseline_target)
            raise
        finally:
            table_backup.unlink(missing_ok=True)
            baseline_backup.unlink(missing_ok=True)

        if promoted:
            ARTIFACTS.mkdir(parents=True, exist_ok=True)
            model_target, card_target = ARTIFACTS / "yield_model.pkl", ARTIFACTS / "model_card.json"
            if model_target.exists() or card_target.exists():
                archive = ARTIFACTS / "archive" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                archive.mkdir(parents=True, exist_ok=False)
                if model_target.exists():
                    shutil.copy2(model_target, archive / "yield_model.pkl")
                if card_target.exists():
                    shutil.copy2(card_target, archive / "model_card.json")
            staged_model = model_target.with_suffix(".pkl.pending")
            staged_card = card_target.with_suffix(".json.pending")
            shutil.copy2(candidate_path, staged_model)
            shutil.copy2(candidate_dir / "model_card.json", staged_card)
            staged_model.replace(model_target)
            staged_card.replace(card_target)
            print("PROMOTED new model; previous validated model and model card archived.")
        else:
            # The source table and baseline have changed, so a prior model
            # trained on the old hash is no longer eligible for serving.
            model_target, card_target = ARTIFACTS / "yield_model.pkl", ARTIFACTS / "model_card.json"
            if model_target.exists() or card_target.exists():
                archive = ARTIFACTS / "archive" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                archive.mkdir(parents=True, exist_ok=False)
                if model_target.exists():
                    shutil.move(str(model_target), archive / model_target.name)
                if card_target.exists():
                    shutil.move(str(card_target), archive / card_target.name)
            print("KEEP BASELINE; the candidate did not clear the held-out improvement margin.")
        drift_path = ROOT / "data" / "eval" / f"drift_{year}_season_{season_code}.json"
        drift_path.parent.mkdir(parents=True, exist_ok=True)
        drift["comparison"] = comparison
        drift["training_winner"] = report.get("winner")
        drift_path.write_text(json.dumps(drift, indent=2, allow_nan=False), encoding="utf-8")
        print(f"Drift report saved: {drift_path}")
        shutil.copytree(evaluation_dir, evaluation_archive)
        shutil.copy2(stage / "audit_flags.csv", evaluation_archive / "audit_flags.csv")
        return {"season": season_label, "rows_added": len(extracted), "winner": report.get("winner"),
                "promoted": promoted, "comparison": comparison, "drift_report": str(drift_path),
                "evaluation_archive": str(evaluation_archive)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--season", choices=("A", "B", "C"), required=True)
    parser.add_argument("--training-table", type=Path, default=TABLE_PATH)
    args = parser.parse_args()
    result = add_new_season(args.pdf, args.year, args.season, args.training_table)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, pd.errors.ParserError) as exc:
        print(f"NEW SEASON INGEST FAILED: {exc}", file=sys.stderr)
        raise SystemExit(2)
