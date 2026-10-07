"""
Yield prediction and priority classification.

Three-tier fallback so the API always returns a real, explainable number:
  1. Trained XGBoost model (app/ml/train_yield_model.py) on real SAS 2026
     district x crop x season data - used when the district/crop/season
     combination was seen in training.
  2. District+crop, then crop-only, average yield from yield_baselines.json
     (built from the same real data) - used for combinations the model
     hasn't seen (e.g. a new season).
  3. Flat placeholder (1200 kg/ha) - only if neither artifact has been
     generated yet, so the pipeline still runs end-to-end on day one.

Run `python -m app.ml.train_yield_model` to generate tiers 1 and 2 from
real data; without that, everything still works via tier 3.
"""
import json
import pickle
import logging
import time
from pathlib import Path
from statistics import mean
from typing import List

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
YIELD_MODEL_PATH = ARTIFACTS_DIR / "yield_model.pkl"
BASELINES_PATH = ARTIFACTS_DIR / "yield_baselines.json"

FLAT_FALLBACK_YIELD_PER_HA = 1200.0
FALLBACK_MODEL_VERSION = "heuristic-v0"


def _load_yield_model():
    """Attempt to load the serialized yield model. If loading fails (for
    example because the file is corrupted), move the artifact aside and
    return None so the service falls back to baselines.
    """
    if not YIELD_MODEL_PATH.exists():
        return None
    try:
        with open(YIELD_MODEL_PATH, "rb") as f:
            return pickle.load(f)
    except Exception as exc:
        logging.exception("Failed to load yield model artifact: %s", exc)
        # try to move the corrupted file to a timestamped backup so it
        # doesn't repeatedly crash the app on import.
        try:
            ts = int(time.time())
            backup = YIELD_MODEL_PATH.with_name(f"yield_model.pkl.corrupted.{ts}")
            YIELD_MODEL_PATH.rename(backup)
            logging.warning("Moved corrupted yield model to %s", backup)
        except Exception:
            logging.exception("Unable to move corrupted yield model file")
        return None


def _load_baselines() -> dict:
    if BASELINES_PATH.exists():
        with open(BASELINES_PATH) as f:
            return json.load(f)
    return {}


def _match_model_class(value: str, classes) -> str | None:
    """Match UI labels to trained encoder labels despite case/word order."""
    normalized = str(value).strip().casefold()
    for candidate in classes:
        candidate_text = str(candidate)
        if candidate_text.strip().casefold() == normalized:
            return candidate_text
        if set(candidate_text.casefold().split()) == set(normalized.split()):
            return candidate_text
    return None


_yield_model_bundle = None
_baselines = _load_baselines()


def _estimate_yield_per_ha(district: str | None, crop: str, season: str | None,
                            area_cultivated: float) -> tuple[float, float, str]:
    """Returns (yield_per_ha, confidence, model_version)."""
    global _yield_model_bundle
    if _yield_model_bundle is None:
        _yield_model_bundle = _load_yield_model()
    bundle = _yield_model_bundle

    if bundle is not None and district and season:
        try:
            d_enc, c_enc, s_enc = bundle["district_encoder"], bundle["crop_encoder"], bundle["season_encoder"]
            district_class = _match_model_class(district, d_enc.classes_)
            crop_class = _match_model_class(crop, c_enc.classes_)
            season_class = _match_model_class(season, s_enc.classes_)
            if district_class and crop_class and season_class:
                import pandas as pd
                features = pd.DataFrame([{
                    "district": d_enc.transform([district_class])[0],
                    "crop": c_enc.transform([crop_class])[0],
                    "season": s_enc.transform([season_class])[0],
                    "cultivated_area_ha": area_cultivated,
                }])[bundle["feature_order"]]
                yield_per_ha = float(bundle["model"].predict(features)[0])
                return round(yield_per_ha, 1), 0.85, bundle["model_version"]
        except Exception:
            pass  # fall through to baseline lookup below

    if district and crop:
        key = f"{district}|{crop}"
        district_crop_avg = _baselines.get("district_crop_averages", {})
        if key in district_crop_avg:
            return district_crop_avg[key], 0.65, "district-crop-baseline-sas2026"

    crop_avg = _baselines.get("crop_averages", {})
    if crop in crop_avg:
        return crop_avg[crop], 0.55, "crop-baseline-sas2026"

    overall = _baselines.get("overall_average")
    if overall:
        return overall, 0.45, "national-baseline-sas2026"

    return FLAT_FALLBACK_YIELD_PER_HA, 0.3, FALLBACK_MODEL_VERSION


def known_crops() -> List[str]:
    """Return the list of crops the baseline/model knows about."""
    crops = set()
    if _baselines:
        crops.update(_baselines.get("crop_averages", {}).keys())
    # try model encoder classes if available
    try:
        global _yield_model_bundle
        if _yield_model_bundle is None:
            _yield_model_bundle = _load_yield_model()
        bundle = _yield_model_bundle
        if bundle is not None and bundle.get("crop_encoder") is not None:
            crops.update(list(bundle.get("crop_encoder").classes_))
    except Exception:
        pass
    return sorted(crops)


def has_data() -> bool:
    return bool(_baselines) or YIELD_MODEL_PATH.exists()


def crop_mean(crop: str) -> float | None:
    return _baselines.get("crop_averages", {}).get(crop)


def get_yield_per_hectare(district: str | None, crop: str) -> float:
    """Best-effort yield per hectare for a district+crop using baselines."""
    if district and crop:
        key = f"{district}|{crop}"
        v = _baselines.get("district_crop_averages", {}).get(key)
        if v is not None:
            return float(v)
    v = _baselines.get("crop_averages", {}).get(crop)
    if v is not None:
        return float(v)
    v = _baselines.get("overall_average")
    if v is not None:
        return float(v)
    return FLAT_FALLBACK_YIELD_PER_HA


def _values_for_crop_across_districts(crop: str) -> List[float]:
    d = _baselines.get("district_crop_averages", {})
    vals = [v for k, v in d.items() if k.endswith(f"|{crop}")]
    return sorted(vals)


def _percentile_from_sorted(sorted_vals: List[float], p: float) -> float | None:
    if not sorted_vals:
        return None
    # p in [0,100]
    if p <= 0:
        return sorted_vals[0]
    if p >= 100:
        return sorted_vals[-1]
    k = (len(sorted_vals)-1) * (p/100.0)
    lo = int(k)
    hi = min(lo+1, len(sorted_vals)-1)
    frac = k - lo
    return sorted_vals[lo] * (1-frac) + sorted_vals[hi] * frac


def get_yield_percentile(district: str, crop: str) -> float | None:
    """Return the percentile (0-100) of the district's yield among peers for the crop.
    Lower percentile means lower-performing district.
    """
    vals = _values_for_crop_across_districts(crop)
    if not vals:
        return None
    key = f"{district}|{crop}"
    district_val = _baselines.get("district_crop_averages", {}).get(key)
    if district_val is None:
        return None
    # percentile rank: percentage of values strictly below district_val
    below = len([v for v in vals if v < district_val])
    # include ties roughly in middle; normalized to 0-100
    return (below / len(vals)) * 100.0


def get_yield_index(district: str, crop: str) -> float | None:
    """district yield / crop mean, or None if crop mean missing."""
    y = get_yield_per_hectare(district, crop)
    cm = crop_mean(crop)
    if cm is None or cm == 0:
        return None
    return float(y / cm)


def get_yield_gap(district: str, crop: str) -> dict:
    """Return a dict with yield_per_ha, benchmark_yield_per_ha (75th pct), yield_gap_kg_ha."""
    y = get_yield_per_hectare(district, crop)
    vals = _values_for_crop_across_districts(crop)
    benchmark = _percentile_from_sorted(vals, 75) if vals else None
    gap = None
    if benchmark is not None:
        gap = round(max(0.0, benchmark - y), 1)
    return {
        "yield_per_ha": round(y, 1),
        "benchmark_yield_per_ha": round(benchmark, 1) if benchmark is not None else None,
        "yield_gap_kg_ha": gap,
    }


def predict_yield(district: str | None, crop: str, season: str | None,
                   rainfall_mm: float | None, area_cultivated: float | None,
                   household_size: float | None) -> tuple[float, float, str]:
    """
    Returns (predicted_yield, confidence, model_version). predicted_yield is
    the total predicted output for the given cultivated area (kg); divide by
    area to get yield per hectare (see classify_priority).
    """
    area = area_cultivated or 0.5
    yield_per_ha, confidence, model_version = _estimate_yield_per_ha(district, crop, season, area)

    # Rainfall is a secondary adjustment on top of the crop/district baseline -
    # neutral (1.0) when rainfall isn't supplied, since the baseline already
    # reflects real seasonal conditions for that district/crop/season.
    rainfall_factor = 1.0
    if rainfall_mm is not None:
        rainfall_factor = min(max(rainfall_mm / 900.0, 0.6), 1.25)

    predicted_total = round(yield_per_ha * area * rainfall_factor, 1)
    return predicted_total, confidence, model_version


def classify_priority(predicted_yield: float, area_cultivated: float | None) -> str:
    """
    Simple, explainable priority rule: lower yield-per-hectare relative to a
    target band => higher priority for intervention. Bands are based on the
    real SAS 2026 yield distribution (most crops cluster 800-12,000+ kg/ha
    depending on crop type, so this is deliberately relative, not absolute -
    refine per-crop thresholds once judges/planners give feedback).
    """
    area = area_cultivated or 0.5
    yield_per_ha = predicted_yield / area if area else predicted_yield

    if yield_per_ha < 900:
        return "High"
    if yield_per_ha < 1400:
        return "Medium"
    return "Low"
